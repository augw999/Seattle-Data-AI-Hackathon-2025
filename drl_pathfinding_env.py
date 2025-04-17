import numpy as np
import gymnasium as gym
from gymnasium import spaces
import random
from config import GRID_WIDTH, GRID_HEIGHT

class DisasterEnv(gym.Env):
    def __init__(self, grid, agent_start, victim_pos, exit_pos):
        super().__init__()
        self.grid = np.array(grid)
        self.agent_pos = list(agent_start)
        self.victim_pos = list(victim_pos)
        self.exit_pos = list(exit_pos)
        self.has_victim = False

        # Define action space: 0 = Up, 1 = Down, 2 = Left, 3 = Right
        self.action_space = spaces.Discrete(4)
        self.observation_space = spaces.Box(
            low=0,
            high=max(GRID_WIDTH, GRID_HEIGHT),
            shape=(6,),
            dtype=np.int32
        )

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.agent_pos = [random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1)]
        self.has_victim = False
        return self._get_obs(), {}

    def _get_obs(self):
        return np.array(self.agent_pos + self.victim_pos + self.exit_pos, dtype=np.int32)

    def step(self, action):
        x, y = self.agent_pos
        if action == 0 and y > 0: y -= 1
        elif action == 1 and y < GRID_HEIGHT - 1: y += 1
        elif action == 2 and x > 0: x -= 1
        elif action == 3 and x < GRID_WIDTH - 1: x += 1

        reward = -1
        terminated = False
        truncated = False

        if self.grid[x][y] == 1:
            reward = -50
            terminated = True
        else:
            self.agent_pos = [x, y]

        if not self.has_victim and self.agent_pos == self.victim_pos:
            self.has_victim = True
            reward = 10

        if self.has_victim and self.agent_pos == self.exit_pos:
            reward = 100
            terminated = True

        return self._get_obs(), reward, terminated, truncated, {}

    def render(self):
        pass
