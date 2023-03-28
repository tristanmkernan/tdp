import pygame
import pygame_gui

from tdp.scenes.enums import SceneKind, SceneEventKind
from tdp.scenes.types import Scene

from .gui import build_gui, cleanup_gui


class MainScene(Scene):
    def setup(self):
        self.gui_elements = build_gui(self.gui_manager)

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
