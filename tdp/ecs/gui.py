import dataclasses

import pygame
import pygame_gui

from tdp.constants import GUI_WIDTH, GUI_HEIGHT, GUI_X_OFFSET, GUI_Y_OFFSET

from .enums import TurretKind
from .resources import TURRET_BUILD_COSTS


@dataclasses.dataclass
class GuiElements:
    panel: pygame_gui.elements.UIPanel
    title: pygame_gui.elements.UILabel

    resources_label: pygame_gui.elements.UILabel

    wave_label: pygame_gui.elements.UILabel
    wave_progress: pygame_gui.elements.UIProgressBar

    basic_turret_build_button: pygame_gui.elements.UIButton
    flame_turret_build_button: pygame_gui.elements.UIButton
    rocket_turret_build_button: pygame_gui.elements.UIButton
    frost_turret_build_button: pygame_gui.elements.UIButton

    clear_turret_build_button: pygame_gui.elements.UIButton


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
        text=f"Basic Turret (${TURRET_BUILD_COSTS[TurretKind.Bullet]})",
        manager=manager,
        container=panel,
        object_id=pygame_gui.core.ObjectID(
            "#basic_turret_build_button", "@turret-build-button--unselected"
        ),
    )

    flame_turret_build_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((10, 160), (panel_width, 20)),
        text=f"Flame Turret (${TURRET_BUILD_COSTS[TurretKind.Flame]})",
        manager=manager,
        container=panel,
        object_id=pygame_gui.core.ObjectID(
            "#flame_turret_build_button", "@turret-build-button--unselected"
        ),
    )

    frost_turret_build_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((10, 180), (panel_width, 20)),
        text=f"Frost Turret (${TURRET_BUILD_COSTS[TurretKind.Frost]})",
        manager=manager,
        container=panel,
        object_id=pygame_gui.core.ObjectID(
            "#frost_turret_build_button", "@turret-build-button--unselected"
        ),
    )

    rocket_turret_build_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((10, 200), (panel_width, 20)),
        text=f"Rocket Turret (${TURRET_BUILD_COSTS[TurretKind.Rocket]})",
        manager=manager,
        container=panel,
        object_id=pygame_gui.core.ObjectID(
            "#rocket_turret_build_button", "@turret-build-button--unselected"
        ),
    )

    clear_turret_build_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((10, 230), (panel_width, 20)),
        text="Clear",
        manager=manager,
        container=panel,
    )

    # TODO selected turret ui (upgrades)

    return GuiElements(
        panel=panel,
        title=title,
        resources_label=resources_label,
        wave_label=wave_label,
        wave_progress=wave_progress,
        basic_turret_build_button=basic_turret_build_button,
        flame_turret_build_button=flame_turret_build_button,
        frost_turret_build_button=frost_turret_build_button,
        rocket_turret_build_button=rocket_turret_build_button,
        clear_turret_build_button=clear_turret_build_button,
    )


def cleanup_gui(gui_elements: GuiElements):
    for field in dataclasses.fields(gui_elements):
        if gui_elem := getattr(gui_elements, field.name, None):
            gui_elem.kill()
