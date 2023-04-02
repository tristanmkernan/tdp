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


def build_gui(gui_manager: pygame_gui.UIManager, map_names: list[str]) -> GuiElements:
    el_width, el_height = 400, 30
    margin = 10
    offset = el_height + margin

    panel_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

    center_x = (SCREEN_WIDTH - el_width) / 2
    center_y = 120

    panel = pygame_gui.elements.UIPanel(
        relative_rect=panel_rect,
        manager=gui_manager,
    )

    title = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect(center_x, center_y, el_width, el_height),
        text="Tower Defense Proto",
        manager=gui_manager,
        container=panel,
    )

    map_selection_dropdown = pygame_gui.elements.UIDropDownMenu(
        map_names,
        map_names[0],
        relative_rect=pygame.Rect(center_x, center_y + offset, el_width, el_height),
        manager=gui_manager,
        container=panel,
    )

    play_game_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(center_x, center_y + offset * 2, el_width, el_height),
        text="Play Game",
        manager=gui_manager,
        container=panel,
    )

    qui_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(center_x, center_y + offset * 3, el_width, el_height),
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
