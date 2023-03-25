import pygame
import pygame_gui

from tdp.constants import SCREEN_HEIGHT, SCREEN_WIDTH
from tdp.ecs.assets import load_assets
from tdp.ecs.enums import InputEventKind
from tdp.ecs.gui import build_gui
from tdp.ecs.world import build_world


def play_game():
    #####
    # setup pygame
    #####

    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    gui_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))

    clock = pygame.time.Clock()

    #####
    # setup world
    #####

    gui_elements = build_gui(gui_manager)
    assets = load_assets()
    world = build_world()

    #####
    # core game loop
    #####

    running = True

    while running:
        time_delta = clock.tick(30)

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

            gui_manager.process_events(event)

        gui_manager.update(time_delta / 1000.0)

        world.process(
            delta=time_delta,
            clock=clock,
            screen=screen,
            gui_manager=gui_manager,
            assets=assets,
            show_fps=True,
            player_input_events=input_events,
            gui_elements=gui_elements,
            debug=False,
        )

    pygame.quit()
