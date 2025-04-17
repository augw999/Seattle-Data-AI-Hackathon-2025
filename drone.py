import time
from config import GRID_WIDTH, GRID_HEIGHT
from pathfinding import a_star

class Drone:
    def __init__(self, x, y, speed=10, sight_range=20):
        self.x = x
        self.y = y
        self.speed = speed
        self.sight_range = sight_range

    def fly(self, target, true_map):
        """
        Fly toward the target using a path planning algorithm.
        """
        route = a_star(true_map["obstacles"], (self.x, self.y), target, agent_mode=True)
        if route and len(route) > 0:
            next_step = route.pop(0)
            self.x, self.y = next_step

    def compute_confidence(self, distance, obstruction):
        """
        Compute confidence: 100% within 5 units, reduce 5% per extra unit, further reduced by obstruction.
        """
        if distance <= 5:
            base = 100
        else:
            base = 100 - 5 * (distance - 5)
        return max(0, base * (1 - obstruction))

    def gather_info(self, true_map):
        """
        Gather information from cells within sight_range.
        Returns a dictionary with timestamp, items, and confidence score per cell.
        """
        info = {}
        current_time = time.time()
        for i in range(max(0, self.x - self.sight_range), min(GRID_WIDTH, self.x + self.sight_range + 1)):
            for j in range(max(0, self.y - self.sight_range), min(GRID_HEIGHT, self.y + self.sight_range + 1)):
                distance = abs(i - self.x) + abs(j - self.y)
                obstruction = true_map["sight"][i][j] / 100.0
                confidence = self.compute_confidence(distance, obstruction)
                info[(i, j)] = {
                    "timestamp": current_time,
                    "items": {
                        "hazard": true_map["hazards"][i][j],
                        "obstacle": true_map["obstacles"][i][j],
                        "safety": true_map["safety"][i][j]
                    },
                    "confidence": confidence
                }
        return info
