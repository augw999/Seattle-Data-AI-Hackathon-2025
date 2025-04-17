import pygame
import random
from config import (GRID_WIDTH, GRID_HEIGHT, INITIAL_HAZARD_COUNT, OBSTACLE_COUNT, SPREAD_OPPORTUNITY,
                    CELL_SIZE, WHITE, RED, GREEN, GRAY, BLACK, LIGHT_RED, MEDIUM_RED, BRIGHT_RED, screen)

def create_map():
    obstacles = [[0 for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)]
    safety = [[0 for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)]
    hazards = [[0 for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)]
    sight_obstruction = [[0 for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)]

    placed = 0
    while placed < OBSTACLE_COUNT:
        x = random.randint(1, GRID_WIDTH - 2)
        y = random.randint(1, GRID_HEIGHT - 2)
        if obstacles[x][y] == 0:
            obstacles[x][y] = 1
            placed += 1

    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            if x == 0 or x == GRID_WIDTH - 1 or y == 0 or y == GRID_HEIGHT - 1:
                safety[x][y] = 1

    placed = 0
    while placed < INITIAL_HAZARD_COUNT:
        x = random.randint(0, GRID_WIDTH - 1)
        y = random.randint(0, GRID_HEIGHT - 1)
        if obstacles[x][y] == 0 and hazards[x][y] == 0:
            hazards[x][y] = random.choice([1, 2, 3])
            placed += 1

    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            level = hazards[x][y]
            if level == 1:
                sight_obstruction[x][y] = max(sight_obstruction[x][y], 20)
            elif level == 2:
                sight_obstruction[x][y] = max(sight_obstruction[x][y], 50)
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if abs(dx) + abs(dy) == 1:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                                sight_obstruction[nx][ny] = max(sight_obstruction[nx][ny], 20)
            elif level == 3:
                sight_obstruction[x][y] = max(sight_obstruction[x][y], 80)
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if abs(dx) + abs(dy) == 1:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                                sight_obstruction[nx][ny] = max(sight_obstruction[nx][ny], 50)
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        if abs(dx) + abs(dy) == 2:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                                sight_obstruction[nx][ny] = max(sight_obstruction[nx][ny], 20)

    return {
        "obstacles": obstacles,
        "safety": safety,
        "hazards": hazards,
        "sight": sight_obstruction
    }

def draw_map(layers):
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            pygame.draw.rect(screen, WHITE, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, GRAY, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)

    obstacles = layers["obstacles"]
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            if obstacles[x][y] == 1:
                pygame.draw.rect(screen, BLACK, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    safety = layers["safety"]
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            if safety[x][y] == 1:
                pygame.draw.rect(screen, GREEN, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    hazards = layers["hazards"]
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            level = hazards[x][y]
            if level == 1:
                color = LIGHT_RED
            elif level == 2:
                color = MEDIUM_RED
            elif level == 3:
                color = BRIGHT_RED
            else:
                continue
            pygame.draw.rect(screen, color, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    sight_obstruction = layers["sight"]
    font = pygame.font.SysFont(None, 18)
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            if sight_obstruction[x][y] > 0:
                text = font.render(f"{sight_obstruction[x][y]}%", True, BLACK)
                screen.blit(text, (x * CELL_SIZE + 2, y * CELL_SIZE + 2))

def evolve_situation(layers):
    new_hazards = [element[:] for element in layers["hazards"]]
    updated = [[False for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)]
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            level = layers["hazards"][x][y]
            if level > 0:
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                            if level == 3:
                                base_multiplier = 1.0
                            elif level == 2:
                                base_multiplier = 0.5
                            elif level == 1:
                                base_multiplier = 0.1
                            if dx == 1 and dy == 1:
                                effective_chance = base_multiplier * SPREAD_OPPORTUNITY
                            else:
                                effective_chance = base_multiplier * SPREAD_OPPORTUNITY * 0.3
                            if random.random() < effective_chance:
                                if new_hazards[nx][ny] < level:
                                    new_hazards[nx][ny] = level
                                    updated[nx][ny] = True
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            if updated[x][y]:
                continue
            level = new_hazards[x][y]
            if level > 0:
                new_level = level
                if random.random() < 0.10 and level < 3:
                    new_level = level + 1
                    updated[x][y] = True
                if random.random() < 0.05 and new_level > 0:
                    new_level = new_level - 1
                    updated[x][y] = True
                new_hazards[x][y] = new_level
    layers["hazards"] = new_hazards
    layers["sight"] = update_sight_layer(new_hazards)

def update_sight_layer(hazards):
    sight_obstruction = [[0 for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)]
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            level = hazards[x][y]
            if level == 1:
                sight_obstruction[x][y] = max(sight_obstruction[x][y], 20)
            elif level == 2:
                sight_obstruction[x][y] = max(sight_obstruction[x][y], 50)
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if abs(dx) + abs(dy) == 1:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                                sight_obstruction[nx][ny] = max(sight_obstruction[nx][ny], 20)
            elif level == 3:
                sight_obstruction[x][y] = max(sight_obstruction[x][y], 80)
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if abs(dx) + abs(dy) == 1:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                                sight_obstruction[nx][ny] = max(sight_obstruction[nx][ny], 50)
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        if abs(dx) + abs(dy) == 2:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                                sight_obstruction[nx][ny] = max(sight_obstruction[nx][ny], 20)
    return sight_obstruction

def find_nearest_safe_zone(grid, x, y):
    from pathfinding import a_star
    min_path = []
    for i in range(GRID_WIDTH):
        for j in range(GRID_HEIGHT):
            if grid[i][j] == 2:
                path = a_star(grid, (x, y), (i, j), agent_mode=True)
                if path and (not min_path or len(path) < len(min_path)):
                    min_path = path
    return min_path[-1] if min_path else None
