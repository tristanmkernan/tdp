import dataclasses

import pygame
import pygame_gui

from tdp.constants import SCREEN_WIDTH, SCREEN_HEIGHT


@dataclasses.dataclass
class GuiElements:
    panel: pygame_gui.elements.UIPanel
    title: pygame_gui.elements.UILabel

    map_selection_dropdown: pygame_gui.elements.UIDropDownMenu
    play_game_button: pygame_gui.elements.UIButton
    quit_button: pygame_gui.elements.UIButton


def build_gui(gui_manager: pygame_gui.UIManager) -> GuiElements:
    panel = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
        manager=gui_manager,
    )

    title = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect(50, 50, 400, 20),
        text="Tower Defense Proto",
        manager=gui_manager,
        container=panel,
    )

    map_selection_dropdown = pygame_gui.elements.UIDropDownMenu(
        # TODO
        ["Map 1", "Map2"],
        "Map 1",
        relative_rect=pygame.Rect(50, 80, 400, 20),
        manager=gui_manager,
        container=panel,
    )

    play_game_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(50, 110, 400, 20),
        text="Play Game",
        manager=gui_manager,
        container=panel,
    )

    qui_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(50, 140, 400, 20),
        text="Quit",
        manager=gui_manager,
        container=panel,
    )

    return GuiElements(
        panel=panel,
        title=title,
        map_selection_dropdown=map_selection_dropdown,
        play_game_button=play_game_button,
        quit_button=qui_button,
    )


def cleanup_gui(gui_elements: GuiElements):
    for field in dataclasses.fields(gui_elements):
        if gui_elem := getattr(gui_elements, field.name, None):
            gui_elem.kill()
