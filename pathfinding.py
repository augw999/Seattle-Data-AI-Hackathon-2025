from queue import PriorityQueue
from config import GRID_WIDTH, GRID_HEIGHT
from stable_baselines3 import DQN
import numpy as np
import os

DRL_MODEL = None
model_path = "drl_disaster_agent.zip"
try:
    if os.path.exists(model_path):
        DRL_MODEL = DQN.load(model_path)
        print(f"✅ Loaded DRL model from {model_path}")
    else:
        print("⚠️ DRL model not found. Using fallback A*.")
except Exception as e:
    print("❌ Failed to load DRL model:", e)

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star(grid, start, goal, agent_mode=False):
    open_set = PriorityQueue()
    open_set.put((0, start))
    came_from = {}
    cost_so_far = {start: 0}
    while not open_set.empty():
        current = open_set.get()[1]
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (current[0] + dx, current[1] + dy)
            if 0 <= neighbor[0] < GRID_WIDTH and 0 <= neighbor[1] < GRID_HEIGHT:
                if grid[neighbor[0]][neighbor[1]] == 1 and not agent_mode:
                    continue
                new_cost = cost_so_far[current] + 1
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + heuristic(goal, neighbor)
                    open_set.put((priority, neighbor))
                    came_from[neighbor] = current
    return []

def drl_next_step(env, obs):
    if DRL_MODEL:
        action, _ = DRL_MODEL.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        return obs[:2] if not done else None
    else:
        print("⚠️ DRL model not loaded; falling back to A*")
        return None
