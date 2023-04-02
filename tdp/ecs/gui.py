import dataclasses

import pygame
import pygame_gui

from tdp.constants import GUI_WIDTH, GUI_HEIGHT, GUI_X_OFFSET, GUI_Y_OFFSET

from .components import TurretMachine
from .enums import TurretKind, TurretUpgradeablePropertyKind
from .resources import TURRET_BUILD_COSTS, TURRET_UPGRADE_COSTS, TURRET_NAMES

from . import esper


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

    selected_turret_panel: pygame_gui.elements.UIPanel
    selected_turret_name_label: pygame_gui.elements.UILabel

    selected_turret_damage_label: pygame_gui.elements.UILabel
    selected_turret_damage_upgrade_button: pygame_gui.elements.UIButton

    selected_turret_rate_of_fire_label: pygame_gui.elements.UILabel
    selected_turret_rate_of_fire_upgrade_button: pygame_gui.elements.UIButton

    selected_turret_range_label: pygame_gui.elements.UILabel
    selected_turret_range_upgrade_button: pygame_gui.elements.UIButton

    game_over_window: pygame_gui.elements.UIWindow
    game_over_score_label: pygame_gui.elements.UILabel
    game_over_main_menu_button: pygame_gui.elements.UIButton


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
        text=f"{TURRET_NAMES[TurretKind.Bullet]} Turret (${TURRET_BUILD_COSTS[TurretKind.Bullet]})",
        manager=manager,
        container=panel,
        object_id=pygame_gui.core.ObjectID(
            "#basic_turret_build_button", "@turret-build-button--unselected"
        ),
    )

    flame_turret_build_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((10, 160), (panel_width, 20)),
        text=f"{TURRET_NAMES[TurretKind.Flame]} Turret (${TURRET_BUILD_COSTS[TurretKind.Flame]})",
        manager=manager,
        container=panel,
        object_id=pygame_gui.core.ObjectID(
            "#flame_turret_build_button", "@turret-build-button--unselected"
        ),
    )

    frost_turret_build_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((10, 180), (panel_width, 20)),
        text=f"{TURRET_NAMES[TurretKind.Frost]} Turret (${TURRET_BUILD_COSTS[TurretKind.Frost]})",
        manager=manager,
        container=panel,
        object_id=pygame_gui.core.ObjectID(
            "#frost_turret_build_button", "@turret-build-button--unselected"
        ),
    )

    rocket_turret_build_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((10, 200), (panel_width, 20)),
        text=f"{TURRET_NAMES[TurretKind.Rocket]} Turret (${TURRET_BUILD_COSTS[TurretKind.Rocket]})",
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

    selected_turret_panel = pygame_gui.elements.UIPanel(
        relative_rect=pygame.Rect((10, 260), (panel_width, 300)),
        container=panel,
        manager=manager,
    )

    selected_turret_panel_width = panel_width - 20
    selected_turret_stat_col_width = selected_turret_panel_width / 2

    selected_turret_name_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((10, 10), (selected_turret_panel_width, 20)),
        text="? Turret",
        manager=manager,
        container=selected_turret_panel,
    )

    selected_turret_damage_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((10, 40), (selected_turret_stat_col_width, 20)),
        text="Damage: 10",
        manager=manager,
        container=selected_turret_panel,
    )

    selected_turret_damage_upgrade_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(
            (selected_turret_stat_col_width + 10, 40),
            (selected_turret_stat_col_width - 10, 20),
        ),
        text=f"++ (${TURRET_UPGRADE_COSTS[TurretUpgradeablePropertyKind.Damage]})",
        manager=manager,
        container=selected_turret_panel,
    )

    selected_turret_rate_of_fire_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((10, 70), (selected_turret_stat_col_width, 20)),
        text="Freq: 10",
        manager=manager,
        container=selected_turret_panel,
    )

    selected_turret_rate_of_fire_upgrade_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(
            (selected_turret_stat_col_width + 10, 70),
            (selected_turret_stat_col_width - 10, 20),
        ),
        text=f"++ (${TURRET_UPGRADE_COSTS[TurretUpgradeablePropertyKind.RateOfFire]})",
        manager=manager,
        container=selected_turret_panel,
    )

    selected_turret_range_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((10, 100), (selected_turret_stat_col_width, 20)),
        text="Range: 10",
        manager=manager,
        container=selected_turret_panel,
    )

    selected_turret_range_upgrade_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect(
            (selected_turret_stat_col_width + 10, 100),
            (selected_turret_stat_col_width - 10, 20),
        ),
        text=f"++ (${TURRET_UPGRADE_COSTS[TurretUpgradeablePropertyKind.Range]})",
        manager=manager,
        container=selected_turret_panel,
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
        relative_rect=pygame.Rect((10, 50), (280, 30)),
        text="Score: ?",
        manager=manager,
        container=game_over_window,
    )

    game_over_main_menu_button = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((10, 90), (280, 30)),
        text="Main Menu",
        manager=manager,
        container=game_over_window,
    )

    # TODO quit button

    # TODO pause button

    # hidden by default
    game_over_window.hide()
    selected_turret_panel.hide()

    ## temporarily disabled
    frost_turret_build_button.hide()

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
        selected_turret_panel=selected_turret_panel,
        selected_turret_name_label=selected_turret_name_label,
        selected_turret_damage_label=selected_turret_damage_label,
        selected_turret_damage_upgrade_button=selected_turret_damage_upgrade_button,
        selected_turret_rate_of_fire_label=selected_turret_rate_of_fire_label,
        selected_turret_rate_of_fire_upgrade_button=selected_turret_rate_of_fire_upgrade_button,
        selected_turret_range_label=selected_turret_range_label,
        selected_turret_range_upgrade_button=selected_turret_range_upgrade_button,
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

    gui_elements.selected_turret_damage_label.set_text(
        f"Damage: {turret.upgrade_levels[TurretUpgradeablePropertyKind.Damage]}"
    )

    gui_elements.selected_turret_rate_of_fire_label.set_text(
        f"Freq: {turret.upgrade_levels[TurretUpgradeablePropertyKind.RateOfFire]}"
    )

    gui_elements.selected_turret_range_label.set_text(
        f"Range: {turret.upgrade_levels[TurretUpgradeablePropertyKind.Range]}"
    )
