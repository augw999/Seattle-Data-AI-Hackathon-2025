import math
from config import GRID_WIDTH, GRID_HEIGHT
from pathfinding import a_star
from map import find_nearest_safe_zone

def compute_route_cost(route, layers):
    """
    Compute a cost for a candidate route.
    Factors: efficiency, hazard cost, and connectivity.
    """
    length = len(route)
    hazard_cost = 0
    connectivity = 0
    for pos in route:
        x, y = pos
        hazard_level = layers["hazards"][x][y]
        if hazard_level == 1:
            hazard_cost += 10
        elif hazard_level == 2:
            hazard_cost += 20
        elif hazard_level == 3:
            hazard_cost += 100
        count = 0
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                if layers["obstacles"][nx][ny] != 1:
                    count += 1
        connectivity += count
    cost = length + hazard_cost - connectivity
    return cost

def compute_optimal_route(start, layers):
    """
    Evaluate candidate routes from start to safety zones.
    Returns the route with the lowest computed cost.
    """
    candidate_exits = []
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            if layers["safety"][x][y] == 1:
                candidate_exits.append((x, y))
    best_route = None
    best_cost = float('inf')
    for exit_pos in candidate_exits:
        route = a_star(layers["obstacles"], start, exit_pos, agent_mode=True)
        if route:
            cost = compute_route_cost(route, layers)
            if cost < best_cost:
                best_cost = cost
                best_route = route
    return best_route

class Commander:
    def __init__(self, danger_radius=10, rescue_area=3, use_rl_selection=False):
        self.danger_radius = danger_radius
        self.rescue_area = rescue_area
        self.use_rl_selection = use_rl_selection
        self.rl_model = None  # Placeholder for an RL model if available

    def compute_danger_level(self, victim, layers):
        """
        Compute the danger level for a victim as the sum over nearby hazard influence.
        """
        total = 0
        for i in range(max(0, victim.x - self.danger_radius), min(GRID_WIDTH, victim.x + self.danger_radius + 1)):
            for j in range(max(0, victim.y - self.danger_radius), min(GRID_HEIGHT, victim.y + self.danger_radius + 1)):
                if layers["hazards"][i][j] > 0:
                    d = abs(victim.x - i) + abs(victim.y - j)
                    if d == 0:
                        d = 1
                    total += layers["hazards"][i][j] / d
        return total

    def compute_self_rescue_score(self, victim, layers):
        """
        Estimate victim’s self-rescue ability based on distance to safety and local free space.
        """
        exit_pos = find_nearest_safe_zone(layers["safety"], victim.x, victim.y)
        if exit_pos is None:
            return 0
        distance = abs(victim.x - exit_pos[0]) + abs(victim.y - exit_pos[1])
        count_free = 0
        total = 0
        for i in range(max(0, victim.x - self.rescue_area), min(GRID_WIDTH, victim.x + self.rescue_area + 1)):
            for j in range(max(0, victim.y - self.rescue_area), min(GRID_HEIGHT, victim.y + self.rescue_area + 1)):
                total += 1
                if layers["obstacles"][i][j] != 1:
                    count_free += 1
        free_ratio = count_free / total if total > 0 else 0
        return free_ratio / (distance + 1)

    def generate_candidate_paths(self, victim, agent, drones, perceived_map):
        """
        Generate candidate paths:
          - From agent to victim (using perceived map)
          - From victim to safety
          (Optionally, drone segments can be added for updated info.)
        """
        path_to_victim = a_star(perceived_map["obstacles"], (agent.x, agent.y), (victim.x, victim.y), agent_mode=True)
        path_to_safety = compute_optimal_route((victim.x, victim.y), perceived_map)
        candidate_paths = []
        if path_to_victim and path_to_safety:
            candidate_paths.append(path_to_victim + path_to_safety)
        return candidate_paths

    def evaluate_path(self, path, victim, agent, perceived_map):
        """
        Evaluate a candidate path with a custom benefit-cost score.
        Here benefit is assumed high (e.g., 100) and cost is summed from hazards.
        """
        benefit = 100
        direct_cost = 0
        for pos in path:
            x, y = pos
            hazard = perceived_map["hazards"][x][y]
            direct_cost += hazard * 5  # arbitrary weighting
        score = benefit - direct_cost
        return score

    def select_task(self, agents, victims, drones, perceived_map):
        """
        For each agent-victim pair, generate candidate paths and choose the task with the highest score.
        If RL is enabled and a model is loaded, use it (stubbed here).
        """
        best_task = None
        best_score = -float('inf')
        for agent in agents:
            if agent.remaining_life <= 0:
                continue
            for victim in victims:
                if victim.rescued or victim.remaining_life <= 0:
                    continue
                candidate_paths = self.generate_candidate_paths(victim, agent, drones, perceived_map)
                if not candidate_paths:
                    continue
                for path in candidate_paths:
                    if self.use_rl_selection and self.rl_model is not None:
                        predicted_score = self.rl_model.predict(path)  # Stub: replace with actual RL inference
                    else:
                        predicted_score = self.evaluate_path(path, victim, agent, perceived_map)
                    if predicted_score > best_score:
                        best_score = predicted_score
                        best_task = {
                            'agent': agent,
                            'victim': victim,
                            'path': path,
                            'score': predicted_score,
                            'target': (victim.x, victim.y)
                        }
        return best_task
