import numpy as np
import random
from collections import deque


class GridEnvironment:
    def __init__(self, grid_size=(7, 22)):
        self.grid_size = grid_size

        # grid 초기화
        self.grid = np.zeros(grid_size)
        self.grid[0, :] = 1
        self.grid[-1, :] = 1
        self.grid[:, 0] = 1
        self.grid[:, -1] = 1

        self.start_pos = [3, 1]
        self.agent_pos = list(self.start_pos)

        self.heading = 0
        self.current_steps = 0
        self.crashed = False

        self.prev_positions = []

        self.small_goal_range = [(1, 20), (5, 20)]

        self.direction_map = {
            0: (0, 1),
            45: (-1, 1),
            90: (-1, 0),
            135: (-1, -1),
            180: (0, -1),
            225: (1, -1),
            270: (1, 0),
            315: (1, 1)
        }

    def reset(self):
        self.generate_valid_map()

        self.agent_pos = list(self.start_pos)
        self.heading = 0
        self.current_steps = 0
        self.crashed = False
        self.prev_positions = []

        return self.get_state()

    # --------------------------
    # 맵 생성 관련
    # --------------------------
    def place_random_obstacles(self, count=30, avoid_area=None):
        placed = 0
        avoid_set = set(avoid_area or [])

        while placed < count:
            x = random.randint(1, self.grid_size[0] - 2)
            y = random.randint(1, self.grid_size[1] - 2)

            if self.grid[x, y] == 0 and (x, y) not in avoid_set:
                self.grid[x, y] = 1
                placed += 1

    def is_path_exists(self, start, goal_cells):
        visited = set()
        queue = deque([tuple(start)])
        visited.add(tuple(start))

        while queue:
            x, y = queue.popleft()

            if (x, y) in goal_cells:
                return True

            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = x + dx, y + dy

                if (
                    0 <= nx < self.grid_size[0] and
                    0 <= ny < self.grid_size[1] and
                    self.grid[nx, ny] == 0 and
                    (nx, ny) not in visited
                ):
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        return False

    def generate_valid_map(self, max_trials=20):
        for _ in range(max_trials):
            self.grid = np.zeros(self.grid_size)

            self.grid[0, :] = 1
            self.grid[-1, :] = 1
            self.grid[:, 0] = 1
            self.grid[:, -1] = 1

            avoid = [tuple(self.start_pos)] + [(x, 20) for x in range(1, 6)]

            count = random.randint(10, 40)
            self.place_random_obstacles(count, avoid)

            goal_cells = [(x, 20) for x in range(1, 6)]

            if self.is_path_exists(self.start_pos, goal_cells):
                return True

        return False

    # --------------------------
    # 센서
    # --------------------------
    def get_sensor_distances(self):
        x, y = self.agent_pos
        heading = self.heading

        angles = [
            (heading - 45) % 360,
            heading % 360,
            (heading + 45) % 360
        ]

        distances = []

        for angle in angles:
            angle = int(round(angle / 45) * 45) % 360
            dx, dy = self.direction_map.get(angle, (0, 1))

            dist = 0
            nx, ny = x, y

            while True:
                nx += dx
                ny += dy
                dist += 1

                if (
                    nx < 0 or nx >= self.grid_size[0] or
                    ny < 0 or ny >= self.grid_size[1] or
                    self.grid[nx, ny] == 1
                ):
                    break

            distances.append(dist)

        return distances

    # --------------------------
    # 상태
    # --------------------------
    def get_state(self):
        return np.array(self.get_sensor_distances(), dtype=np.float32)

    # --------------------------
    # 목표
    # --------------------------
    def is_goal(self, x, y):
        return (
            self.small_goal_range[0][0] <= x <= self.small_goal_range[1][0]
            and y == self.small_goal_range[0][1]
        )

    # --------------------------
    # step
    # --------------------------
    def step(self, action):
        self.current_steps += 1

        x, y = self.agent_pos
        reward = -0.1

        if action == 0:
            self.heading = (self.heading + 45) % 360

        elif action == 1:
            heading = int(round(self.heading / 45) * 45) % 360
            dx, dy = self.direction_map.get(heading, (0, 1))

            nx, ny = x + dx, y + dy

            if (
                0 <= nx < self.grid_size[0] and
                0 <= ny < self.grid_size[1] and
                self.grid[nx, ny] == 0
            ):
                x, y = nx, ny
                reward += 1
            else:
                return self.get_state(), -10, True, {}

        elif action == 2:
            self.heading = (self.heading - 45) % 360

        self.agent_pos = [x, y]

        # 반복 위치 패널티
        self.prev_positions.append((x, y))
        if len(self.prev_positions) > 8:
            self.prev_positions.pop(0)

        if self.prev_positions.count((x, y)) >= 4:
            return self.get_state(), -5, True, {}

        # 목표 도달
        if self.is_goal(x, y):
            return self.get_state(), 50, True, {}

        # 제한
        if self.current_steps > 100:
            return self.get_state(), -10, True, {}

        return self.get_state(), reward, False, {}