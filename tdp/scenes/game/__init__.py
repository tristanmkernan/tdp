import pygame
import pygame_gui

from tdp.ecs.assets import load_assets
from tdp.ecs.enums import InputEventKind
from tdp.ecs.gui import build_gui, cleanup_gui
from tdp.ecs.world import build_world
from tdp.scenes.enums import SceneEventKind

from tdp.scenes.types import Scene


class GameScene(Scene):
    def setup(self):
        self.gui_elements = build_gui(self.gui_manager)
        self.assets = load_assets()
        self.world = build_world()

    def run(self):
        running = True

        while running:
            time_delta = self.clock.tick(30)

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
                    case pygame_gui.UI_BUTTON_PRESSED:
                        input_events.append(
                            {
                                "kind": InputEventKind.UIButtonPress,
                                "ui_element": event.ui_element,
                            }
                        )

                self.gui_manager.process_events(event)

            self.gui_manager.update(time_delta / 1000.0)

            self.world.process(
                delta=time_delta,
                clock=self.clock,
                screen=self.screen,
                gui_manager=self.gui_manager,
                assets=self.assets,
                show_fps=True,
                player_input_events=input_events,
                gui_elements=self.gui_elements,
                debug=False,
            )

        return {"kind": SceneEventKind.Quit}

    def cleanup(self):
        cleanup_gui(self.gui_elements)
