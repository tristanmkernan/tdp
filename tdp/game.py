import pygame

from tdp.constants import SCREEN_HEIGHT, SCREEN_WIDTH
from tdp.ecs.assets import load_assets
from tdp.ecs.enums import InputEventKind
from tdp.ecs.world import build_world


def play_game():
    #####
    # setup pygame
    #####

    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    clock = pygame.time.Clock()

    #####
    # setup world
    #####

    assets = load_assets()
    world = build_world()

    #####
    # core game loop
    #####

    running = True

    while running:
        input_events = []

        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    running = False
                case pygame.KEYDOWN:
                    input_events.append(
                        {"kind": InputEventKind.KeyDown, "key": event.key}
                    )
                case pygame.KEYUP:
                    input_events.append(
                        {"kind": InputEventKind.KeyUp, "key": event.key}
                    )
                case pygame.MOUSEBUTTONUP:
                    if event.button == pygame.BUTTON_LEFT:
                        input_events.append(
                            {
                                "kind": InputEventKind.MouseLeftClickUp,
                                "pos": event.pos,
                            }
                        )

        ms = clock.tick(30)

        world.process(
            delta=ms,
            clock=clock,
            screen=screen,
            assets=assets,
            show_fps=True,
            player_input_events=input_events,
            debug=False,
        )

    pygame.quit()
