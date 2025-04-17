import pygame
import random
import math
import time
from config import CELL_SIZE, GRID_WIDTH, GRID_HEIGHT, BLUE, YELLOW
from map import find_nearest_safe_zone  # used in guidance
from pathfinding import a_star           # used for full route planning

def move_towards(x, y, tx, ty, max_steps):
    """
    Moves from (x, y) toward (tx, ty) by at most max_steps in Manhattan distance.
    Returns the new coordinates.
    """
    dx = tx - x
    dy = ty - y
    if abs(dx) + abs(dy) <= max_steps:
        return (tx, ty)
    new_x, new_y = x, y
    steps = max_steps
    while steps > 0 and (new_x != tx or new_y != ty):
        if abs(tx - new_x) >= abs(ty - new_y):
            new_x += 1 if tx - new_x > 0 else -1
        else:
            new_y += 1 if ty - new_y > 0 else -1
        steps -= 1
    return (new_x, new_y)

class Agent:
    def __init__(self, x, y, speed=3, remaining_life=100, sight_distance=5, mode="autonomous"):
        self.x = x                                              # grid x-coordinate
        self.y = y                                              # grid y-coordinate
        self.speed = speed                                      # normal movement speed (cells per move)
        self.remaining_life = remaining_life                    # percentage (0-100)
        self.sight_distance = sight_distance                    # maximum Manhattan distance for clear sight
        self.base_sight = {1: 100, 2: 80, 3: 60, 4: 50, 5: 40}   # Base sight percentages for Manhattan distances
        self.alive = True                                       # Flag to mark if the agent is alive
        self.guided_victims = []                                # List of victims currently being guided
        self.guiding_speed = max(1, speed - 1)                  # Reduced speed when guiding
        self.mode = mode                                        # "autonomous" or "ordered"
        self.current_task = None                                # Task assigned by a Commander (if any)

    def move(self, target, layers):
        """
        Moves toward the target coordinate one cell at a time.
        Uses guiding_speed if the agent is currently guiding victims.
        Does not step into obstacles.
        """
        if not self.alive or self.remaining_life <= 0:
            return
        current_speed = self.guiding_speed if self.guided_victims else self.speed
        total_distance = abs(target[0] - self.x) + abs(target[1] - self.y)
        steps = min(current_speed, total_distance)
        for i in range(steps):
            next_pos = move_towards(self.x, self.y, target[0], target[1], 1)
            if layers["obstacles"][next_pos[0]][next_pos[1]] == 1:
                print(f"Agent blocked by obstacle at {next_pos}")
                break
            self.x, self.y = next_pos
            self.apply_hazard_damage(layers)
            if self.remaining_life <= 0:
                self.alive = False
                break

    def render(self, screen):
        if not self.alive or self.remaining_life <= 0:
            return
        pygame.draw.circle(
            screen,
            BLUE,
            (self.x * CELL_SIZE + CELL_SIZE // 2, self.y * CELL_SIZE + CELL_SIZE // 2),
            10
        )
        font = pygame.font.SysFont(None, 18)
        life_text = font.render(f"{self.remaining_life}%", True, (0, 0, 0))
        screen.blit(life_text, (self.x * CELL_SIZE, self.y * CELL_SIZE - 10))
        if self.guided_victims:
            guide_text = font.render(f"Guiding {len(self.guided_victims)}", True, (255, 255, 255))
            screen.blit(guide_text, (self.x * CELL_SIZE, self.y * CELL_SIZE + 10))

    def get_effective_sight(self, target, layers):
        dx = target[0] - self.x
        dy = target[1] - self.y
        steps = max(abs(dx), abs(dy))
        if steps == 0:
            return 100
        base = self.base_sight.get(min(steps, self.sight_distance), 0)
        max_obstruction = 0
        for i in range(1, steps):
            inter_x = self.x + round(i * dx / steps)
            inter_y = self.y + round(i * dy / steps)
            obs = layers["sight"][inter_x][inter_y]
            if obs > max_obstruction:
                max_obstruction = obs
        effective = max(0, base * (1 - max_obstruction))
        return effective

    def rescue_victim(self, layers, victims):
        """
        In autonomous mode, scans for the nearest non-rescued victim (not being guided)
        within effective sight. Uses A* to compute a full route to bypass obstacles/hazards
        and moves one step along that route. When adjacent, adds the victim to guided_victims,
        sets victim.being_guided to True, and begins guiding the victim toward safety.
        In ordered mode, follows current_task.
        """
        if not self.alive or self.remaining_life <= 0:
            return
        if self.mode == "ordered":
            self.follow_task(layers)
            return
        min_dist = math.inf
        candidate = None
        for victim in victims:
            if not victim.rescued and not victim.being_guided:
                effective = self.get_effective_sight((victim.x, victim.y), layers)
                if effective > 35:
                    d = abs(victim.x - self.x) + abs(victim.y - self.y)
                    if d < min_dist:
                        min_dist = d
                        candidate = victim
        if candidate is not None:
            # Compute full route using A* to bypass obstacles
            route = a_star(layers["obstacles"], (self.x, self.y), (candidate.x, candidate.y), agent_mode=True)
            if route and len(route) > 0:
                next_step = route.pop(0)
                self.move(next_step, layers)
            if abs(candidate.x - self.x) + abs(candidate.y - self.y) <= 1:
                if candidate not in self.guided_victims:
                    self.guided_victims.append(candidate)
                    candidate.being_guided = True
                    print(f"Agent at ({self.x},{self.y}) now guiding victim at ({candidate.x},{candidate.y})")
                self.guide_victims(layers)
                candidate.x, candidate.y = self.x, self.y
                if layers["safety"][self.x][self.y] == 1:
                    candidate.rescued = True
                    print(f"Victim rescued at ({self.x},{self.y})")
        else:
            self.search_for_victims(layers)

    def follow_task(self, layers):
        """
        Follows the current task assigned by a Commander.
        The task should contain a 'target' coordinate (destination) and a 'route'
        which is a full route computed (via A*) that bypasses obstacles and hazards.
        If the next step in the route becomes blocked, the route is recalculated.
        """
        if self.current_task is None:
            return
        target = self.current_task.get('target')  # target coordinate (x,y)
        route = self.current_task.get('route')
        if not route or len(route) == 0 or layers["obstacles"][route[0][0]][route[0][1]] == 1:
            route = a_star(layers["obstacles"], (self.x, self.y), target, agent_mode=True)
            if route is None:
                self.current_task = None
                return
            self.current_task['route'] = route
        next_step = route.pop(0)
        self.move(next_step, layers)
        if not route:
            self.current_task = None

    def guide_victims(self, layers):
        """
        Guides all currently guided victims toward a safety zone.
        Uses guiding_speed for movement. Computes an exit route using A*.
        Updates all guided victims' positions to match the agent's new position.
        Once a safety zone is reached, marks victims as rescued and clears guided_victims.
        """
        exit_zone = find_nearest_safe_zone(layers["safety"], self.x, self.y)
        if exit_zone is None:
            return
        route = a_star(layers["obstacles"], (self.x, self.y), exit_zone, agent_mode=True)
        if route and len(route) > 0:
            next_step = route[0]
            self.move(next_step, layers)
            for victim in self.guided_victims:
                victim.x, victim.y = self.x, self.y
                if layers["safety"][self.x][self.y] == 1:
                    victim.rescued = True
                    victim.being_guided = False
                    print(f"Guided victim rescued at ({self.x},{self.y})")
            if layers["safety"][self.x][self.y] == 1:
                self.guided_victims = []

    def search_for_victims(self, layers):
        """
        When no victim is visible, moves away from safety zones to search for victims.
        """
        if not self.alive or self.remaining_life <= 0:
            return
        safety_positions = []
        for dx in range(-self.sight_distance, self.sight_distance + 1):
            for dy in range(-self.sight_distance, self.sight_distance + 1):
                nx = self.x + dx
                ny = self.y + dy
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                    if layers["safety"][nx][ny] == 1:
                        safety_positions.append((nx, ny))
        if safety_positions:
            nearest = min(safety_positions, key=lambda t: abs(t[0]-self.x) + abs(t[1]-self.y))
            dir_x = self.x - nearest[0]
            dir_y = self.y - nearest[1]
            move_x = 1 if dir_x > 0 else -1 if dir_x < 0 else 0
            move_y = 1 if dir_y > 0 else -1 if dir_y < 0 else 0
            candidate = (self.x + move_x, self.y + move_y)
            if 0 <= candidate[0] < GRID_WIDTH and 0 <= candidate[1] < GRID_HEIGHT:
                if layers["obstacles"][candidate[0]][candidate[1]] != 1:
                    self.x, self.y = candidate
                    self.apply_hazard_damage(layers)
        else:
            candidate_moves = []
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                    if layers["obstacles"][nx][ny] != 1:
                        candidate_moves.append((nx, ny))
            if candidate_moves:
                new_pos = random.choice(candidate_moves)
                self.x, self.y = new_pos
                self.apply_hazard_damage(layers)

    def self_rescue(self, layers):
        """
        When not actively rescuing or guiding a victim, if hazards are present or safety is visible,
        moves toward safety or away from hazards.
        """
        if not self.alive or self.remaining_life <= 0:
            return
        safety_targets = []
        hazard_visible = False
        for dx in range(-self.sight_distance, self.sight_distance + 1):
            for dy in range(-self.sight_distance, self.sight_distance + 1):
                nx = self.x + dx
                ny = self.y + dy
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                    manhattan = abs(dx) + abs(dy)
                    if manhattan == 0 or manhattan > self.sight_distance:
                        continue
                    effective = self.get_effective_sight((nx, ny), layers)
                    if effective > 35:
                        if layers["safety"][nx][ny] == 1:
                            safety_targets.append((nx, ny))
                        if layers["hazards"][nx][ny] > 0:
                            hazard_visible = True
        if safety_targets:
            target = min(safety_targets, key=lambda t: abs(t[0]-self.x)+abs(t[1]-self.y))
            self.move(target, layers)
        elif hazard_visible:
            candidate_moves = []
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                    if layers["obstacles"][nx][ny] != 1:
                        candidate_moves.append((nx, ny))
            if candidate_moves:
                new_pos = random.choice(candidate_moves)
                self.x, self.y = new_pos
                self.apply_hazard_damage(layers)

    def apply_hazard_damage(self, layers):
        if self.remaining_life <= 0:
            return
        hazard_level = layers["hazards"][self.x][self.y]
        if hazard_level == 1:
            self.remaining_life -= 5
        elif hazard_level == 2:
            self.remaining_life -= 10
        elif hazard_level == 3:
            self.remaining_life -= 50
        if self.remaining_life < 0:
            self.remaining_life = 0
            if layers["safety"][self.x][self.y] != 1:
                self.alive = False

    def report_local_info(self, true_map):
        """
        Rescuer reporting function: scans cells within self.sight_distance and reports
        information (timestamp, items, confidence score) with a smaller range.
        """
        info = {}
        current_time = time.time()
        for i in range(max(0, self.x - self.sight_distance), min(GRID_WIDTH, self.x + self.sight_distance + 1)):
            for j in range(max(0, self.y - self.sight_distance), min(GRID_HEIGHT, self.y + self.sight_distance + 1)):
                distance = abs(i - self.x) + abs(j - self.y)
                if distance <= 3:
                    base = 100
                else:
                    base = 100 - 5 * (distance - 3)
                obstruction = true_map["sight"][i][j] / 100.0
                confidence = max(0, base * (1 - obstruction))
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

class Victim:
    def __init__(self, x, y, sight_distance=3, remaining_life=100):
        self.x = x
        self.y = y
        self.rescued = False
        self.being_guided = False  # Lock flag when being guided.
        self.sight_distance = sight_distance
        self.remaining_life = remaining_life
        self.base_sight = {1: 100, 2: 70, 3: 40}
        self.rescued_by = None

    def render(self, screen):
        pygame.draw.circle(
            screen,
            YELLOW,
            (self.x * CELL_SIZE + CELL_SIZE // 2, self.y * CELL_SIZE + CELL_SIZE // 2),
            8
        )

    def get_effective_sight(self, target, layers):
        dx = target[0] - self.x
        dy = target[1] - self.y
        steps = max(abs(dx), abs(dy))
        if steps == 0:
            return 100
        base = self.base_sight.get(min(steps, self.sight_distance), 0)
        max_obstruction = 0
        for i in range(1, steps):
            inter_x = self.x + round(i * dx / steps)
            inter_y = self.y + round(i * dy / steps)
            obs = layers["sight"][inter_x][inter_y]
            if obs > max_obstruction:
                max_obstruction = obs
        effective = max(0, base - max_obstruction)
        return effective

    def self_rescue(self, layers):
        if self.remaining_life <= 0 or self.rescued or self.being_guided:
            return
        safety_targets = []
        hazard_positions = []
        for dx in range(-self.sight_distance, self.sight_distance + 1):
            for dy in range(-self.sight_distance, self.sight_distance + 1):
                nx = self.x + dx
                ny = self.y + dy
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                    manhattan = abs(dx) + abs(dy)
                    if manhattan == 0 or manhattan > self.sight_distance:
                        continue
                    effective = self.get_effective_sight((nx, ny), layers)
                    if effective > 35:
                        if layers["safety"][nx][ny] == 1:
                            safety_targets.append((nx, ny))
                        if layers["hazards"][nx][ny] > 0:
                            hazard_positions.append((nx, ny))
        if safety_targets:
            target = min(safety_targets, key=lambda t: abs(t[0]-self.x)+abs(t[1]-self.y))
            new_pos = move_towards(self.x, self.y, target[0], target[1], 1)
            if layers["obstacles"][new_pos[0]][new_pos[1]] != 1:
                self.x, self.y = new_pos
            self.apply_hazard_damage(layers)
            if layers["safety"][self.x][self.y] == 1 and not self.rescued:
                self.rescued = True
                print(f"Victim reached safety at ({self.x},{self.y})")
        elif hazard_positions:
            avg_x = sum(pos[0] for pos in hazard_positions) / len(hazard_positions)
            avg_y = sum(pos[1] for pos in hazard_positions) / len(hazard_positions)
            dir_x = self.x - avg_x
            dir_y = self.y - avg_y
            move_x = 1 if dir_x > 0 else -1 if dir_x < 0 else 0
            move_y = 1 if dir_y > 0 else -1 if dir_y < 0 else 0
            candidate = (self.x + move_x, self.y + move_y)
            if 0 <= candidate[0] < GRID_WIDTH and 0 <= candidate[1] < GRID_HEIGHT:
                if layers["obstacles"][candidate[0]][candidate[1]] != 1:
                    self.x, self.y = candidate
            self.apply_hazard_damage(layers)

    def apply_hazard_damage(self, layers):
        if self.remaining_life <= 0:
            return
        hazard_level = layers["hazards"][self.x][self.y]
        if hazard_level == 1:
            self.remaining_life -= 10
        elif hazard_level == 2:
            self.remaining_life -= 20
        elif hazard_level == 3:
            self.remaining_life -= 100
        if self.remaining_life < 0:
            self.remaining_life = 0
