import pygame

# Grid settings
GRID_WIDTH = 75
GRID_HEIGHT = 50
CELL_SIZE = 15
INITIAL_HAZARD_COUNT = 20
OBSTACLE_COUNT = 800
SPREAD_OPPORTUNITY = 0.1

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (169, 169, 169)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
LIGHT_RED = (255, 200, 200)
MEDIUM_RED = (255, 100, 100)
BRIGHT_RED = (255, 0, 0)

# Initialize Pygame screen
pygame.init()
screen = pygame.display.set_mode((GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE))
pygame.display.set_caption("Disaster Response Simulation")
