import glob

import pygame
import pygame_gui

from tdp.scenes.enums import SceneKind, SceneEventKind
from tdp.scenes.types import Scene

from .gui import build_gui, cleanup_gui


def get_map_names() -> list[str]:
    extension = ".tdp.tmx"

    folder = "./assets/maps/"

    map_names = []

    for filename in glob.glob(f"{folder}*{extension}"):
        map_names.append(filename.rsplit("/", 1)[1].removesuffix(extension))

    return map_names


class MainScene(Scene):
    def setup(self):
        map_names = get_map_names()
        self.gui_elements = build_gui(self.gui_manager, map_names)

    def run(self):
        running = True

        while running:
            time_delta = self.clock.tick(30)

            for event in pygame.event.get():
                match event.type:
                    case pygame.QUIT:
                        running = False
                    case pygame_gui.UI_BUTTON_PRESSED:
                        match event.ui_element:
                            case self.gui_elements.play_game_button:
                                selected_map = (
                                    self.gui_elements.map_selection_dropdown.selected_option
                                )

                                return {
                                    "kind": SceneEventKind.ChangeScene,
                                    "to": SceneKind.Game,
                                    "map": selected_map,
                                }
                            case self.gui_elements.quit_button:
                                return {"kind": SceneEventKind.Quit}

                self.gui_manager.process_events(event)

            self.gui_manager.update(time_delta / 1000.0)

            self.screen.fill((255, 255, 255))

            self.gui_manager.draw_ui(self.screen)

            pygame.display.flip()

        return {
            "kind": SceneEventKind.Quit,
        }

    def cleanup(self):
        cleanup_gui(self.gui_elements)
