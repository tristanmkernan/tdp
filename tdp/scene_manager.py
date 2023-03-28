import pygame
import pygame_gui

from tdp.constants import SCREEN_HEIGHT, SCREEN_WIDTH

from tdp.scenes.enums import SceneKind, SceneEventKind
from tdp.scenes import GameScene, MainScene, Scene


def start_app():
    #####
    # setup pygame
    #####

    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    gui_manager = pygame_gui.UIManager(
        (SCREEN_WIDTH, SCREEN_HEIGHT), "assets/theme.json"
    )

    clock = pygame.time.Clock()

    #####
    # setup scenes
    #####

    scenes_map = {SceneKind.Main: MainScene, SceneKind.Game: GameScene}

    current_scene: Scene = MainScene(
        screen=screen, gui_manager=gui_manager, clock=clock
    )

    running = True

    while running:
        # run() can return transitions or exit the game
        match current_scene.run():
            case {"kind": SceneEventKind.Quit}:
                running = False
            case {"kind": SceneEventKind.ChangeScene, "to": scene_kind}:
                current_scene.cleanup()
                current_scene = scenes_map[scene_kind](
                    screen=screen, gui_manager=gui_manager, clock=clock
                )
            case _:
                pass

    pygame.quit()
