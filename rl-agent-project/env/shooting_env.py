from collections import deque
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random
import matplotlib.pyplot as plt
import gc  # 가비지 컬렉션
import time

goal_reached = 0 # 목표지점 도달 횟수

'''
입력값 상대거리

출력값 행동
0: 좌, 1: 우, 2: 정지, 3: 발사
'''

# ================================
# 그리드 좌표 매핑 (행, 열) = (y, x)
#     열 인덱스 →
# 행   0   1   2   3   4   5  ... 21
# ↓  -------------------------------
# 0 |(0,0)(0,1)(0,2)(0,3)(0,4)(0,5)...
# 1 |(1,0)(1,1)(1,2)(1,3)(1,4)(1,5)...
# 2 | ...
# 6 |(6,0)(6,1)(6,2)(6,3)(6,4)(6,5)...
# ================================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

class GridEnvironment:
    def __init__(self, grid_size=(30, 10)):
        self.grid_size = grid_size
        self.grid = np.zeros(grid_size)
        self.grid[0, :] = 1 # 상단 벽
        self.grid[-1, :] = 1        # 하단 벽
        self.grid[:, 0] = 1       # 좌측 벽
        self.grid[:, -1] = 1    # 우측 벽

        self.hit_count = 0
        #self.grid[4:7, 4:7] = 1
        self.agent_pos = [28, 4] # 시작 위치
        self.start_pos = list(self.agent_pos)

        self.current_steps = 0

        self.bullet_List = []
        self.bullet_speed = 2
        self.bulletnum = 0
        # 시각화를 위한 속성 추가
        self.position = self.agent_pos
        self.start = self.start_pos
        self.prevPosition = []
        self.small_goal_range = [[1, 3], [1, 5]]
    

    def reset(self):
        self.agent_pos = list(self.start_pos)
        self.position = self.agent_pos

        self.bullet_List = []
        self.current_steps = 0
        self.bulletnum = 0
        self.hit_count = 0



        return self.get_state()
        
    
    def move_bullet_forward(self):
        goal_x_min = self.small_goal_range[0][0]
        goal_x_max = self.small_goal_range[1][0]
        goal_y_min = self.small_goal_range[0][1]
        goal_y_max = self.small_goal_range[1][1]

        new_bullet_list = []
        hit = 0

        for bullet in self.bullet_List:
            old_x, y = bullet
            new_x = old_x - self.bullet_speed

            # 🔍 총알 경로 중에 목표를 지나쳤는지 확인
            passed_x = range(min(old_x, new_x), max(old_x, new_x) + 1)
            if any(x in passed_x for x in range(goal_x_min, goal_x_max + 1)) and goal_y_min <= y <= goal_y_max:
                hit = 1
                self.bulletnum -= 1
                self.hit_count += 1
            elif new_x > 0:
                bullet[0] = new_x
                new_bullet_list.append(bullet)
            else:
                self.bulletnum -= 1
                hit = -1

        self.bullet_List = new_bullet_list
        return hit

    
    def move_bullet_by_action(self, action):
        # 총알을 이동시키는 메서드
        for bullet in self.bullet_List:
            x, y = bullet
            if action == 0:  # 좌로 이동
                y -= 1
            elif action == 1:  # 우로 이동
                y += 1
            elif action == 2:  # 정지
                pass
            bullet[0] = x
            bullet[1] = y





        

    def move_goal_by_random(self):
        # 목표 위치를 무작위로 이동
        randnum = random.randint(0, 2)  # 0: 좌, 1: 우, 2: 정지

        # 목표 영역의 최소/최대 x(=열 인덱스) 계산
        goal_y_min = self.small_goal_range[0][1]
        goal_y_max = self.small_goal_range[1][1]

        if randnum == 0:  # 좌로 이동
            if goal_y_min > 1:  # 좌측 벽을 넘지 않도록
                for goal in self.small_goal_range:
                    goal[1] -= 1

        elif randnum == 1:  # 우로 이동
            if goal_y_max < self.grid_size[1] - 2:  # 우측 벽 전까지만 이동
                for goal in self.small_goal_range:
                    goal[1] += 1

        else:  # 정지
            pass



    '''def get_state(self):
        agent_y, agent_x = self.agent_pos

        goal_x_min = self.small_goal_range[0][1]
        goal_x_max = self.small_goal_range[1][1]
        goal_x_center = (goal_x_min + goal_x_max) / 2

        dx = goal_x_center - agent_x  # 가로 거리 계산
        return np.array([dx], dtype=np.float32)'''


    def get_state(self):
        agent_y, agent_x = self.agent_pos

        goal_x_min = self.small_goal_range[0][1]
        goal_x_max = self.small_goal_range[1][1]
        goal_x_center = (goal_x_min + goal_x_max) / 2

        dx = goal_x_center - agent_x
        dx_norm = dx / (self.grid_size[1] - 1)
        goal_center_norm = goal_x_center / (self.grid_size[1] - 1)
        bullets_norm = self.bulletnum / 8.0  # 8발 제한 기준

        return np.array([dx_norm, goal_center_norm, bullets_norm], dtype=np.float32)




    
    def step(self, action):
        self.current_steps += 1
        #x, y = self.agent_pos
        
        x,y = self.agent_pos  # 주의: (y, x) 순서입니다!
        reward = -1
        if action == 0:  # 좌로 한 칸
            if y > 1:  # 벽 안쪽이면 이동 허용
                #print("좌", y)
                y -= 1
                #self.move_bullet_by_action(action)
            else:
                pass
                #print("좌측 벽에 막힘")

        elif action == 1:  # 우로 한 칸
            if y < self.grid_size[1] - 2:  # 우측 벽 전에만 이동
                #print("우", y)
                y += 1
                #self.move_bullet_by_action(action)
            else:
                pass
                #print("우측 벽에 막힘")

        elif action == 2:  # 제자리리
            #print("정지", y)
            pass
        elif action == 3:  # 발사
            if self.bulletnum > 7:  # 발사 가능 총알 수 제한
                #print("발사 불가", self.bulletnum)
                #reward -= 1
                pass
            else:
                self.bulletnum += 1
                #print("발사", y)
                self.bullet_List.append([x, y])

            # 디버깅 정보 출력
            #print(f"Action: {action}, Heading: {self.heading}, Position: {x, y}")

        
        self.agent_pos = [x, y]
        
        

        

        reached = self.move_bullet_forward()

        if reached == 1: # 총알이 목표에 도달
            reward += 30
            #return self.get_state(), reward, True, {}

        if reached == -1: # 총알이 화면 밖으로 나감
            reward -= 4

        if self.hit_count >= 30:
            
            #print("목표 도달")
            return self.get_state(), reward, True, {}

        self.move_goal_by_random()

        if self.current_steps >= 100:
            
            return self.get_state(), reward, True, {}

        

        return self.get_state(), reward, False, {}
    




class DQN(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(DQN, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim)
        )

    def forward(self, x):
        return self.fc(x)
 
def visualize_episode_steps(env, model, episode_num, fig=None, ax=None):
    state = env.reset()
    done = False
    path = [env.agent_pos.copy()]  # [y, x]
    rewards = []
    bullet_snapshots = [env.bullet_List.copy()]
    goal_snapshots = [ [g.copy() for g in env.small_goal_range] ]  # ✅ goal 위치 기록
    bullet_counts = [env.bulletnum]  # 총알 개수 기록
    while not done and env.current_steps < 100:
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
        with torch.no_grad():
            q_values = model(state_tensor)
        action = q_values.argmax().item()
        next_state, reward, done, _ = env.step(action)

        path.append(env.agent_pos.copy())
        rewards.append(reward)
        bullet_snapshots.append([b.copy() for b in env.bullet_List])  # ✅ 총알 복사 저장
        goal_snapshots.append([g.copy() for g in env.small_goal_range])  # ✅ goal 복사 저장
        bullet_counts.append(env.bulletnum)  # 매 step마다 저장
        state = next_state

    for step in range(len(path)):
        ax[0].clear()
        grid_display = np.zeros(env.grid_size)

        # 벽 시각화
        grid_display[env.grid == 1] = 0.7

        # ✅ 골 영역 시각화 (스텝별 위치)
        x1, y1 = goal_snapshots[step][0]
        x2, y2 = goal_snapshots[step][1]
        grid_display[x1:x2+1, y1:y2+1] = 0.3

        ax[0].imshow(grid_display, cmap='Greys', alpha=0.5)

        # 이동 경로 시각화
        if step > 0:
            path_coords = np.array(path[:step+1])
            ax[0].plot(path_coords[:, 1], path_coords[:, 0], 'b-', alpha=0.7)
            for pos_y, pos_x in path[:step]:
                ax[0].plot(pos_x, pos_y, 'bo', alpha=0.3, markersize=6)

        # 현재 위치
        cy, cx = path[step]
        ax[0].plot(cx, cy, 'r*', markersize=15, label='Agent')

        # 총알 시각화
        for bullet_y, bullet_x in bullet_snapshots[step]:
            ax[0].plot(bullet_x, bullet_y, 'ks', markersize=6)

        # 격자선
        for i in range(env.grid_size[0]):
            ax[0].axhline(y=i+0.5, color='black', linewidth=0.5, alpha=0.3)
        for j in range(env.grid_size[1]):
            ax[0].axvline(x=j+0.5, color='black', linewidth=0.5, alpha=0.3)

        ax[0].set_xticks(range(env.grid_size[1]))
        ax[0].set_yticks(range(env.grid_size[0]))
        ax[0].grid(False)
        current_bullets = bullet_counts[step]
        cumulative_reward = sum(rewards[:step]) if step > 0 else 0
        ax[0].set_title(f'Episode {episode_num+1}, Step {step}/{len(path)-1}\n'
                        f'Agent Pos: ({cy},{cx}),Bullets: {current_bullets}, Reward: {cumulative_reward:.1f}')
        ax[0].legend()
        plt.draw()
        plt.pause(0.05)

    gc.collect()
    return path, rewards





def train_dqn_with_visualization(env, max_episodes=6000, enable_visualization=False):
    state_dim = len(env.get_state())
    action_dim = 4  # 좌, 우, 정지, 발사

    model = DQN(state_dim, action_dim).to(device)
    target_model = DQN(state_dim, action_dim).to(device)
    target_model.load_state_dict(model.state_dict())

    optimizer = optim.Adam(model.parameters(), lr=0.0003)
    criterion = nn.MSELoss()

    replay_buffer = []
    max_buffer_size = 20000
    batch_size = 256
    gamma = 0.99

    epsilon = 1.0
    epsilon_min = 0.1
    epsilon_decay = 0.9995
    target_update = 10

    # 시각화용 설정
    if enable_visualization:
        plt.ion()
        fig, ax = plt.subplots(1, 2, figsize=(16, 8))

    rewards_history = []
    steps_history = []
    hit_history = deque(maxlen=50)
    best_hit_count = -1
    save_interval = 25
    visualization_interval = 1000

    for episode in range(max_episodes):
        state = env.reset()
        done = False
        total_reward = 0

        while not done:
            if random.random() < epsilon:
                action = random.randint(0, action_dim - 1)
            else:
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
                with torch.no_grad():
                    q_values = model(state_tensor)
                action = q_values.argmax().item()

            next_state, reward, done, _ = env.step(action)
            total_reward += reward

            replay_buffer.append((state, action, reward, next_state, done))
            if len(replay_buffer) > max_buffer_size:
                replay_buffer.pop(0)

            state = next_state

            if len(replay_buffer) >= batch_size:
                batch = random.sample(replay_buffer, batch_size)
                states, actions, rewards_b, next_states, dones = zip(*batch)

                states = torch.FloatTensor(np.array(states)).to(device)
                next_states = torch.FloatTensor(np.array(next_states)).to(device)
                actions = torch.LongTensor(actions).unsqueeze(1).to(device)
                rewards_b = torch.FloatTensor(rewards_b).to(device)
                dones = torch.FloatTensor(dones).to(device)

                current_q_values = model(states).gather(1, actions).squeeze()
                with torch.no_grad():
                    next_q_values = target_model(next_states).max(1)[0]
                    target_q_values = rewards_b + (1 - dones) * gamma * next_q_values

                loss = criterion(current_q_values, target_q_values)
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()

        epsilon = max(epsilon * epsilon_decay, epsilon_min)

        if episode % target_update == 0:
            target_model.load_state_dict(model.state_dict())

        rewards_history.append(total_reward)
        steps_history.append(env.current_steps)
        hit_history.append(env.hit_count)

        # 최고 명중 모델 저장
        if env.hit_count > best_hit_count:
            best_hit_count = env.hit_count
            torch.save(model.state_dict(), "best_model.pth")
            print(f"🎯 Best model saved! Hit Count = {best_hit_count}")

        # 평균 히트 기반 조기 종료
        if len(hit_history) == hit_history.maxlen:
            avg_hits = np.mean(hit_history)
            if avg_hits >= 20:
                print(f"✅ Early stop: Recent Avg Hit Count = {avg_hits:.2f}")
                break

        # 시각화
        if enable_visualization and (episode + 1) % visualization_interval == 0:
            ax[1].clear()
            ax[1].plot(rewards_history, label='Reward', alpha=0.7)
            ax[1].plot(steps_history, label='Steps', alpha=0.7)
            ax[1].set_xlabel('Episode')
            ax[1].set_ylabel('Value')
            ax[1].legend()
            ax[1].grid(True)
            ax[1].set_title('Training Progress')
            plt.draw()
            plt.pause(0.01)

            visualize_episode_steps(env, model, episode, fig, ax)

            if (episode + 1) % save_interval == 0:
                plt.close('all')
                plt.figure()
                plt.close()
                fig, ax = plt.subplots(1, 2, figsize=(16, 8))
                plt.ion()
                gc.collect()
                time.sleep(0.5)

        elif (episode + 1) % 100 == 0:
            avg_reward = np.mean(rewards_history[-10:])
            avg_steps = np.mean(steps_history[-10:])
            print(f"Episode {episode+1}: Avg R={avg_reward:.2f}, Avg Steps={avg_steps:.1f}, Epsilon={epsilon:.2f}")

    if enable_visualization:
        plt.ioff()
        plt.close('all')

    torch.save(model.state_dict(), "슈팅_총알제한.pth")
    print("학습 완료 및 최종 모델 저장됨.")

    return model

# 학습 실행
if __name__ == "__main__":
    env = GridEnvironment()
    trained_model = train_dqn_with_visualization(env, max_episodes=6000, enable_visualization=False)
    print(f"Total goal reached: {goal_reached} times")