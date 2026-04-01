import os
import random
from collections import deque

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt

from env.obstacle_env import GridEnvironment
from model.dqn import DQN, ReplayBuffer


# --------------------------------------------------
# Device
# --------------------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# --------------------------------------------------
# Seed
# 연구 재현성을 위해 seed 고정 옵션 제공
# --------------------------------------------------
def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# --------------------------------------------------
# DQN update
# target network를 사용해 학습 안정성을 높임
# --------------------------------------------------
def train_step(
    model: DQN,
    target_model: DQN,
    replay_buffer: ReplayBuffer,
    optimizer: optim.Optimizer,
    batch_size: int,
    gamma: float,
) -> float | None:
    if len(replay_buffer) < batch_size:
        return None

    states, actions, rewards, next_states, dones = replay_buffer.sample(batch_size)

    states = torch.FloatTensor(states).to(device)
    actions = torch.LongTensor(actions).unsqueeze(1).to(device)
    rewards = torch.FloatTensor(rewards).to(device)
    next_states = torch.FloatTensor(next_states).to(device)
    dones = torch.FloatTensor(dones).to(device)

    current_q = model(states).gather(1, actions).squeeze(1)

    with torch.no_grad():
        next_q = target_model(next_states).max(1)[0]
        target_q = rewards + (1 - dones) * gamma * next_q

    loss = nn.MSELoss()(current_q, target_q)

    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step()

    return loss.item()


# --------------------------------------------------
# Plot save
# reward / step 추세를 남겨서 포트폴리오 자료로 활용
# --------------------------------------------------
def save_training_plot(reward_history, step_history, save_path: str) -> None:
    plt.figure(figsize=(10, 5))
    plt.plot(reward_history, label="Episode Reward")
    plt.plot(step_history, label="Episode Steps", alpha=0.7)
    plt.xlabel("Episode")
    plt.ylabel("Value")
    plt.title("Training History")
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()


# --------------------------------------------------
# Main training loop
# --------------------------------------------------
def train_obstacle_agent(
    episodes: int = 3000,
    batch_size: int = 128,
    gamma: float = 0.99,
    learning_rate: float = 3e-4,
    buffer_size: int = 20000,
    target_update_interval: int = 20,
    epsilon_start: float = 1.0,
    epsilon_min: float = 0.05,
    epsilon_decay: float = 0.995,
    seed: int = 42,
):
    set_seed(seed)

    env = GridEnvironment()
    state_dim = len(env.reset())
    action_dim = 3  # obstacle env: 회전/전진 3개 행동

    model = DQN(state_dim, action_dim).to(device)
    target_model = DQN(state_dim, action_dim).to(device)
    target_model.load_state_dict(model.state_dict())
    target_model.eval()

    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    replay_buffer = ReplayBuffer(capacity=buffer_size)

    epsilon = epsilon_start

    reward_history = []
    step_history = []
    loss_history = []
    recent_rewards = deque(maxlen=50)

    best_reward = -float("inf")

    os.makedirs("results/models", exist_ok=True)
    os.makedirs("results/plots", exist_ok=True)

    for episode in range(1, episodes + 1):
        state = env.reset()
        done = False
        total_reward = 0.0
        episode_loss = []

        while not done:
            # epsilon-greedy:
            # 초기에는 탐색 위주, 이후 점차 exploitation 비중 증가
            if random.random() < epsilon:
                action = random.randint(0, action_dim - 1)
            else:
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
                with torch.no_grad():
                    q_values = model(state_tensor)
                action = q_values.argmax(dim=1).item()

            next_state, reward, done, _ = env.step(action)

            replay_buffer.push(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward

            loss = train_step(
                model=model,
                target_model=target_model,
                replay_buffer=replay_buffer,
                optimizer=optimizer,
                batch_size=batch_size,
                gamma=gamma,
            )
            if loss is not None:
                episode_loss.append(loss)

        epsilon = max(epsilon_min, epsilon * epsilon_decay)

        if episode % target_update_interval == 0:
            target_model.load_state_dict(model.state_dict())

        reward_history.append(total_reward)
        step_history.append(env.current_steps)
        recent_rewards.append(total_reward)

        mean_loss = float(np.mean(episode_loss)) if episode_loss else 0.0
        loss_history.append(mean_loss)

        # 최고 성능 모델 저장
        if total_reward > best_reward:
            best_reward = total_reward
            torch.save(model.state_dict(), "results/models/best_obstacle_model.pth")

        # 중간 저장
        if episode % 500 == 0:
            torch.save(model.state_dict(), f"results/models/obstacle_model_ep{episode}.pth")
            save_training_plot(
                reward_history,
                step_history,
                "results/plots/obstacle_training_progress.png",
            )

        # 로그
        recent_avg = float(np.mean(recent_rewards))
        print(
            f"[Episode {episode:4d}/{episodes}] "
            f"Reward: {total_reward:7.2f} | "
            f"Steps: {env.current_steps:3d} | "
            f"Epsilon: {epsilon:.3f} | "
            f"Avg(50): {recent_avg:7.2f} | "
            f"Loss: {mean_loss:.4f}"
        )

    # 최종 모델 저장
    torch.save(model.state_dict(), "results/models/final_obstacle_model.pth")
    save_training_plot(
        reward_history,
        step_history,
        "results/plots/obstacle_training_final.png",
    )

    return {
        "model": model,
        "reward_history": reward_history,
        "step_history": step_history,
        "loss_history": loss_history,
    }


if __name__ == "__main__":
    train_obstacle_agent()