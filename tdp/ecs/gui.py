import dataclasses

import pygame
import pygame_gui

from tdp.constants import GUI_WIDTH, GUI_HEIGHT, GUI_X_OFFSET, GUI_Y_OFFSET

from .components import TurretMachine
from .enums import TurretKind, TurretUpgradeablePropertyKind, enabled_turret_kinds
from .resources import (
    TURRET_BUILD_COSTS,
    TURRET_SELL_REWARD,
    TURRET_UPGRADE_COSTS,
    TURRET_NAMES,
    TURRET_UPGRADE_NAMES,
)

from . import esper


@dataclasses.dataclass
class GuiElements:
    panel: pygame_gui.elements.UIPanel
    title: pygame_gui.elements.UILabel

    resources_label: pygame_gui.elements.UILabel

    wave_label: pygame_gui.elements.UILabel
    wave_progress: pygame_gui.elements.UIProgressBar

    turret_build_buttons: dict[TurretKind, pygame_gui.elements.UIButton]

    clear_turret_build_button: pygame_gui.elements.UIButton

    selected_turret_panel: pygame_gui.elements.UIPanel
    selected_turret_name_label: pygame_gui.elements.UILabel

    selected_turret_property_labels: dict[
        TurretUpgradeablePropertyKind, pygame_gui.elements.UILabel
    ]
    selected_turret_property_upgrade_buttons: dict[
        TurretUpgradeablePropertyKind, pygame_gui.elements.UIButton
    ]

    selected_turret_sell_button: pygame_gui.elements.UIButton

    game_over_window: pygame_gui.elements.UIPanel
    game_over_score_label: pygame_gui.elements.UILabel
    game_over_main_menu_button: pygame_gui.elements.UIButton


def build_gui(manager: pygame_gui.UIManager) -> GuiElements:
    panel = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect(GUI_X_OFFSET, GUI_Y_OFFSET, GUI_WIDTH, GUI_HEIGHT),
        manager=manager,
    )

    panel_width = GUI_WIDTH - 32
    subpanel_width = panel_width - 8

    title = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((10, 20), (panel_width, 20)),
        text="Tower Defense Proto",
        manager=manager,
        container=panel,
    )

    wave_panel = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect((10, 60), (panel_width, 48)),
        manager=manager,
        container=panel,
    )

    wave_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((2, 0), (subpanel_width, 20)),
        text="Wave ...",
        manager=manager,
        container=wave_panel,
    )
    wave_progress = pygame_gui.elements.UIProgressBar(
        relative_rect=pygame.Rect((2, 0), (subpanel_width, 20)),
        manager=manager,
        container=wave_panel,
        anchors={"top_target": wave_label},
    )

    # turret selection
    build_turret_panel = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect((10, 10), (panel_width, 210)),
        manager=manager,
        container=panel,
        anchors={"top_target": wave_panel},
    )

    build_turret_panel_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((2, 0), (subpanel_width, 20)),
        text="Turrets",
        manager=manager,
        container=build_turret_panel,
    )

    resources_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((2, 0), (subpanel_width, 20)),
        text="Money: ...",
        manager=manager,
        container=build_turret_panel,
        anchors={"top_target": build_turret_panel_label},
    )

    previous_turret_build_button = None
    turret_build_buttons = {}

    for turret_kind in enabled_turret_kinds:
        anchors = {"top_target": resources_label}

        if previous_turret_build_button is not None:
            anchors = {"top_target": previous_turret_build_button}

        turret_build_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((2, 0), (subpanel_width, 24)),
            text=f"{TURRET_NAMES[turret_kind]} (${TURRET_BUILD_COSTS[turret_kind]})",
            manager=manager,
            container=build_turret_panel,
            anchors=anchors,
        )

        turret_build_buttons[turret_kind] = turret_build_button

        previous_turret_build_button = turret_build_button

    clear_turret_build_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((2, 0), (subpanel_width, 24)),
        text="Clear",
        manager=manager,
        container=build_turret_panel,
        anchors={"top_target": previous_turret_build_button},
    )

    selected_turret_panel = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect((10, 10), (panel_width, 300)),
        container=panel,
        manager=manager,
        anchors={"top_target": build_turret_panel},
    )

    selected_turret_stat_col_width = subpanel_width / 2

    selected_turret_name_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((10, 8), (subpanel_width, 20)),
        text="? Turret",
        manager=manager,
        container=selected_turret_panel,
    )

    upgradeable_properties = [
        TurretUpgradeablePropertyKind.Damage,
        TurretUpgradeablePropertyKind.RateOfFire,
        TurretUpgradeablePropertyKind.Range,
    ]

    previous_upgradeable_property_container = None

    selected_turret_property_labels = {}
    selected_turret_property_upgrade_buttons = {}

    for upgradeable_property in upgradeable_properties:
        anchors = {"top_target": selected_turret_name_label}

        if previous_upgradeable_property_container is not None:
            anchors = {"top_target": previous_upgradeable_property_container}

        selected_turret_property_container = pygame_gui.core.UIContainer(
            relative_rect=pygame.Rect((0, 0), (subpanel_width, 24)),
            manager=manager,
            container=selected_turret_panel,
            anchors=anchors,
        )

        selected_turret_property_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 0), (selected_turret_stat_col_width, 20)),
            text=f"{TURRET_UPGRADE_NAMES[upgradeable_property]}: ?",
            manager=manager,
            container=selected_turret_property_container,
        )

        selected_turret_property_upgrade_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (selected_turret_stat_col_width + 10, 0),
                (selected_turret_stat_col_width - 10, 20),
            ),
            text=f"++ (${TURRET_UPGRADE_COSTS[TurretUpgradeablePropertyKind.Damage]})",
            manager=manager,
            container=selected_turret_property_container,
        )

        selected_turret_property_labels[
            upgradeable_property
        ] = selected_turret_property_label
        selected_turret_property_upgrade_buttons[
            upgradeable_property
        ] = selected_turret_property_upgrade_button

        previous_upgradeable_property_container = selected_turret_property_container

    selected_turret_sell_turret_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((0, -24), (subpanel_width, 24)),
        text="Recycle ($?)",
        manager=manager,
        container=selected_turret_panel,
        anchors={"bottom": "bottom"},
    )

    game_over_window = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect((300, 300), (300, 180)),
        manager=manager,
    )

    game_over_title_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((10, 10), (280, 30)),
        text="Game Over",
        manager=manager,
        container=game_over_window,
    )

    game_over_score_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((10, 0), (280, 30)),
        text="Score: ?",
        manager=manager,
        container=game_over_window,
        anchors={"top_target": game_over_title_label},
    )

    game_over_main_menu_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((10, 0), (280, 30)),
        text="Main Menu",
        manager=manager,
        container=game_over_window,
        anchors={"top_target": game_over_score_label},
    )

    # TODO quit button

    # TODO pause button

    # hidden by default
    game_over_window.hide()
    selected_turret_panel.hide()

    return GuiElements(
        panel=panel,
        title=title,
        resources_label=resources_label,
        wave_label=wave_label,
        wave_progress=wave_progress,
        turret_build_buttons=turret_build_buttons,
        clear_turret_build_button=clear_turret_build_button,
        selected_turret_panel=selected_turret_panel,
        selected_turret_name_label=selected_turret_name_label,
        selected_turret_property_labels=selected_turret_property_labels,
        selected_turret_property_upgrade_buttons=selected_turret_property_upgrade_buttons,
        selected_turret_sell_button=selected_turret_sell_turret_button,
        game_over_window=game_over_window,
        game_over_score_label=game_over_score_label,
        game_over_main_menu_button=game_over_main_menu_button,
    )


def cleanup_gui(gui_elements: GuiElements):
    for field in dataclasses.fields(gui_elements):
        if gui_elem := getattr(gui_elements, field.name, None):
            gui_elem.kill()


def sync_selected_turret_gui(
    world: esper.World, turret_ent: int, gui_elements: GuiElements
):
    turret = world.component_for_entity(turret_ent, TurretMachine)

    gui_elements.selected_turret_name_label.set_text(
        f"{TURRET_NAMES[turret.kind]} Turret"
    )

    gui_elements.selected_turret_sell_button.set_text(
        f"Recycle (${TURRET_SELL_REWARD})"
    )

    upgradeable_properties = [
        TurretUpgradeablePropertyKind.Damage,
        TurretUpgradeablePropertyKind.RateOfFire,
        TurretUpgradeablePropertyKind.Range,
    ]

    for upgradeable_property in upgradeable_properties:
        gui_elements.selected_turret_property_labels[upgradeable_property].set_text(
            f"{TURRET_UPGRADE_NAMES[upgradeable_property]}: {turret.upgrade_levels[upgradeable_property]}"
        )
