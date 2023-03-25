import dataclasses

import pygame
import pygame_gui

from tdp.constants import GUI_WIDTH, GUI_HEIGHT, GUI_X_OFFSET, GUI_Y_OFFSET


@dataclasses.dataclass
class GuiElements:
    resources_label: pygame_gui.elements.UILabel

    wave_label: pygame_gui.elements.UILabel
    wave_progress: pygame_gui.elements.UIProgressBar


def build_gui(manager: pygame_gui.UIManager) -> GuiElements:
    panel = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect(GUI_X_OFFSET, GUI_Y_OFFSET, GUI_WIDTH, GUI_HEIGHT),
        manager=manager,
    )

    panel_width = GUI_WIDTH - 32

    title = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((10, 20), (panel_width, 20)),
        text="Tower Defense Proto",
        manager=manager,
        container=panel,
    )

    wave_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((10, 60), (panel_width, 20)),
        text="Wave ...",
        manager=manager,
        container=panel,
    )
    wave_progress = pygame_gui.elements.UIProgressBar(
        relative_rect=pygame.Rect((10, 80), (panel_width, 20)),
        manager=manager,
        container=panel,
    )

    # turret selection
    resources_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((10, 120), (panel_width, 20)),
        text="Money: ...",
        manager=manager,
        container=panel,
    )

    basic_turret_build_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((10, 140), (panel_width, 20)),
        text="Basic Turret ($50)",
        manager=manager,
        container=panel,
    )

    flame_turret_build_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((10, 160), (panel_width, 20)),
        text="Flame Turret ($100)",
        manager=manager,
        container=panel,
    )

    rocket_turret_build_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((10, 180), (panel_width, 20)),
        text="Rocket Turret ($100)",
        manager=manager,
        container=panel,
    )

    # TODO selected turret ui (upgrades)

    return GuiElements(
        resources_label=resources_label,
        wave_label=wave_label,
        wave_progress=wave_progress,
    )
