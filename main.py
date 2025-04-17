import pygame
import random
from config import screen, GRID_WIDTH, GRID_HEIGHT
from map import create_map, draw_map, evolve_situation
from agent import Agent, Victim
from commander import Commander
from pathfinding import a_star, drl_next_step
from drl_pathfinding_env import DisasterEnv
from drone import Drone
from communicator import Communicator
from ethics_checker import EthicsChecker
from communication_log import log_message

# Constants
NUM_AGENTS = 3
NUM_VICTIMS = 50
NUM_DRONES = 5
TOTAL_ROUNDS = 1000

def pause_simulation(screen):
    paused = True
    font = pygame.font.SysFont(None, 48)
    pause_text = font.render("Paused - Press P to resume", True, (255, 255, 255))
    while paused:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = False
        screen.fill((0, 0, 0))
        screen.blit(pause_text, (50, 50))
        pygame.display.flip()

def print_final_results(victims, agents, rounds, sim_name):
    # Count victims rescued by themselves, rescued by agents, and those that died.
    self_rescued = sum(1 for victim in victims if victim.rescued and victim.rescued_by == "self")
    agent_rescued = sum(1 for victim in victims if victim.rescued and victim.rescued_by == "agent")
    victims_died = sum(1 for victim in victims if not victim.rescued and victim.remaining_life <= 0)
    agents_died = sum(1 for agent in agents if agent.remaining_life <= 0)
    agents_survived = NUM_AGENTS - agents_died

    print(f"{sim_name} Simulation Ended after {rounds} rounds")
    print("Victims rescued by themselves:", self_rescued)
    print("Victims rescued by rescuers:", agent_rescued)
    print("Victims died:", victims_died)
    print("Rescuers survived:", agents_survived)
    print("Rescuers died:", agents_died)

def game_loop_baseline():
    # Baseline: victims and rescuers act on their own.
    layers = create_map()
    agents = [Agent(random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
              for _ in range(NUM_AGENTS)]
    victims = [Victim(random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
               for _ in range(NUM_VICTIMS)]
    round_count = 0
    clock = pygame.time.Clock()

    while round_count < TOTAL_ROUNDS:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                pause_simulation(screen)

        round_count += 1
        if round_count % 5 == 0:
            evolve_situation(layers)

        # Victim behavior
        for victim in victims:
            if not victim.rescued:
                if victim.remaining_life > 0:
                    prev_v_pos = (victim.x, victim.y)
                    victim.self_rescue(layers)
                    # If no movement, take a random valid step.
                    if (victim.x, victim.y) == prev_v_pos:
                        candidate_moves = []
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nx, ny = victim.x + dx, victim.y + dy
                            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                                if layers["obstacles"][nx][ny] != 1:
                                    candidate_moves.append((nx, ny))
                        if candidate_moves:
                            new_pos = random.choice(candidate_moves)
                            victim.x, victim.y = new_pos
                            victim.apply_hazard_damage(layers)
                    if layers["safety"][victim.x][victim.y] == 1:
                        victim.rescued = True
                        # Mark as self-rescued if not already guided.
                        if victim.rescued_by is None:
                            victim.rescued_by = "self"
                else:
                    victim.rescued = True

        if all(v.rescued for v in victims):
            break

        # Agent behavior
        for agent in agents:
            if agent.remaining_life > 0:
                prev_pos = (agent.x, agent.y)
                agent.rescue_victim(layers, victims)
                if (agent.x, agent.y) == prev_pos:
                    agent.search_for_victims(layers)
                    if (agent.x, agent.y) == prev_pos:
                        candidate_moves = []
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nx, ny = agent.x + dx, agent.y + dy
                            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                                if layers["obstacles"][nx][ny] != 1:
                                    candidate_moves.append((nx, ny))
                        if candidate_moves:
                            new_pos = random.choice(candidate_moves)
                            agent.x, agent.y = new_pos
                            agent.apply_hazard_damage(layers)
                agent.self_rescue(layers)

        screen.fill((0, 0, 0))
        draw_map(layers)
        for agent in agents:
            if agent.remaining_life > 0:
                agent.render(screen)
        for victim in victims:
            if not victim.rescued:
                victim.render(screen)
        pygame.display.flip()
        clock.tick(10)

    print_final_results(victims, agents, round_count, "Baseline")
    pygame.quit()

def game_loop_non_rl_guidance():
    # Guidance with Commander AI without reinforced learning.
    layers = create_map()
    drones = [Drone(random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
              for _ in range(NUM_DRONES)]
    agents = [Agent(random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1), mode="ordered")
              for _ in range(NUM_AGENTS)]
    victims = [Victim(random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
               for _ in range(NUM_VICTIMS)]

    communicator = Communicator(layers, use_rl_prediction=False)
    commander = Commander(use_rl_selection=False)
    ethics_checker = EthicsChecker()

    round_count = 0
    clock = pygame.time.Clock()
    for agent in agents:
        agent.current_task = None

    while round_count < TOTAL_ROUNDS:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                pause_simulation(screen)
        round_count += 1
        if round_count % 5 == 0:
            evolve_situation(layers)

        # Drones gather info.
        for drone in drones:
            drone_report = drone.gather_info(layers)
            communicator.update_from_report(drone_report)

        # Agents report local info.
        for agent in agents:
            if agent.alive:
                agent_report = agent.report_local_info(layers)
                communicator.update_from_report(agent_report)

        communicator.update_perceived_map()

        task = commander.select_task(agents, victims, drones, communicator.perceived_map)
        if task:
            approved_task = ethics_checker.check_decision(task)
            log_message(approved_task)
            agent_assigned = approved_task['agent']
            agent_assigned.current_task = approved_task

        for agent in agents:
            if not agent.alive:
                continue
            prev_pos = (agent.x, agent.y)
            if agent.mode == "ordered" and agent.current_task:
                route = agent.current_task.get('route', [])
                if route and len(route) > 0:
                    next_step = route.pop(0)
                    agent.move(next_step, layers)
                target_victim = agent.current_task.get('victim')
                if target_victim and abs(agent.x - target_victim.x) + abs(agent.y - target_victim.y) <= 1:
                    if target_victim not in agent.guided_victims:
                        agent.guided_victims.append(target_victim)
                    agent.guide_victims(layers)
                    target_victim.x, target_victim.y = agent.x, agent.y
                    if layers["safety"][agent.x][agent.y] == 1:
                        target_victim.rescued = True
                        target_victim.rescued_by = "agent"
                        agent.current_task = None
            else:
                agent.rescue_victim(layers, victims)
            agent.self_rescue(layers)

        screen.fill((0, 0, 0))
        draw_map(layers)
        for agent in agents:
            if agent.alive:
                agent.render(screen)
        for victim in victims:
            if not victim.rescued:
                victim.render(screen)
        pygame.display.flip()
        clock.tick(10)

        if all(v.rescued or v.remaining_life <= 0 for v in victims):
            break

    print_final_results(victims, agents, round_count, "Non-RL Guidance")
    pygame.quit()

def game_loop_rl_guidance():
    # Guidance with Commander AI with reinforced learning enabled.
    layers = create_map()
    drones = [Drone(random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
              for _ in range(NUM_DRONES)]
    agents = [Agent(random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1), mode="ordered")
              for _ in range(NUM_AGENTS)]
    victims = [Victim(random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
               for _ in range(NUM_VICTIMS)]

    communicator = Communicator(layers, use_rl_prediction=True)
    commander = Commander(use_rl_selection=True)
    ethics_checker = EthicsChecker()

    round_count = 0
    clock = pygame.time.Clock()
    for agent in agents:
        agent.current_task = None

    while round_count < TOTAL_ROUNDS:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                pause_simulation(screen)
        round_count += 1
        if round_count % 5 == 0:
            evolve_situation(layers)

        for drone in drones:
            drone_report = drone.gather_info(layers)
            communicator.update_from_report(drone_report)

        for agent in agents:
            if agent.alive:
                agent_report = agent.report_local_info(layers)
                communicator.update_from_report(agent_report)

        communicator.update_perceived_map()

        task = commander.select_task(agents, victims, drones, communicator.perceived_map)
        if task:
            approved_task = ethics_checker.check_decision(task)
            log_message(approved_task)
            agent_assigned = approved_task['agent']
            agent_assigned.current_task = approved_task

        for agent in agents:
            if not agent.alive:
                continue
            prev_pos = (agent.x, agent.y)
            if agent.mode == "ordered" and agent.current_task:
                route = agent.current_task.get('route', [])
                if route and len(route) > 0:
                    next_step = route.pop(0)
                    agent.move(next_step, layers)
                target_victim = agent.current_task.get('victim')
                if target_victim and abs(agent.x - target_victim.x) + abs(agent.y - target_victim.y) <= 1:
                    if target_victim not in agent.guided_victims:
                        agent.guided_victims.append(target_victim)
                    agent.guide_victims(layers)
                    target_victim.x, target_victim.y = agent.x, agent.y
                    if layers["safety"][agent.x][agent.y] == 1:
                        target_victim.rescued = True
                        target_victim.rescued_by = "agent"
                        print(f"Victim rescued at ({agent.x},{agent.y}) by Commander order.")
                        agent.current_task = None
            else:
                agent.rescue_victim(layers, victims)
            agent.self_rescue(layers)

        screen.fill((0, 0, 0))
        draw_map(layers)
        for agent in agents:
            if agent.alive:
                agent.render(screen)
        for victim in victims:
            if not victim.rescued:
                victim.render(screen)
        pygame.display.flip()
        clock.tick(10)

        if all(v.rescued or v.remaining_life <= 0 for v in victims):
            break

    print_final_results(victims, agents, round_count, "RL Guidance")
    pygame.quit()

def main_menu():
    print("Select Simulation Version:")
    print("1: Baseline - No guidance")
    print("2: Non-Reinforced-Learning Guidance")
    print("3: Reinforced-Learning Guidance")
    choice = input("Enter 1, 2, or 3: ")
    return choice

if __name__ == "__main__":
    version = main_menu()
    if version == "1":
        game_loop_baseline()
    elif version == "2":
        game_loop_non_rl_guidance()
    elif version == "3":
        game_loop_rl_guidance()
    else:
        print("Invalid selection. Exiting.")
