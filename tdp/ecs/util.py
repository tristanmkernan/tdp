import logging

from pygame.math import Vector2

from tdp.ecs.gui import GuiElements

from .components import (
    BoundingBox,
    PathGraph,
    TurretBuildZone,
    Enemy,
    TurretMachine,
    UnitPathing,
)
from .types import PlayerAction
from .enums import (
    PlayerActionKind,
    ResearchKind,
    enabled_turret_kinds,
    TurretUpgradeablePropertyKind,
)

from . import esper

logger = logging.getLogger(__name__)


def get_player_action_for_click(world: esper.World, pos) -> PlayerAction | None:
    # for now, just look for selecting turret build zones
    for ent, (bbox, bz) in world.get_components(BoundingBox, TurretBuildZone):
        if bbox.rect.collidepoint(pos):
            return {"kind": PlayerActionKind.SelectTurretBuildZone, "ent": ent}

    for ent, (bbox, turret_machine) in world.get_components(BoundingBox, TurretMachine):
        if bbox.rect.collidepoint(pos):
            return {"kind": PlayerActionKind.SelectTurret, "ent": ent}

    return None


def get_player_action_for_button_press(
    world: esper.World, ui_element, gui_elements: GuiElements
) -> PlayerAction | None:
    for turret_kind in enabled_turret_kinds:
        if ui_element == gui_elements.turret_build_buttons[turret_kind]:
            return {
                "kind": PlayerActionKind.SetTurretToBuild,
                "turret_kind": turret_kind,
            }

    for upgradeable_property in TurretUpgradeablePropertyKind:
        if ui_element == gui_elements.selected_turret_property_upgrade_buttons.get(
            upgradeable_property
        ):
            return {
                "kind": PlayerActionKind.UpgradeTurretProperty,
                "turret_property": upgradeable_property,
            }

    for research_kind in ResearchKind:
        if ui_element == gui_elements.research_buttons[research_kind]:
            return {
                "kind": PlayerActionKind.StartResearch,
                "research_kind": research_kind,
            }

    match ui_element:
        case gui_elements.selected_turret_sell_button:
            return {
                "kind": PlayerActionKind.SellTurret,
            }
        case gui_elements.clear_turret_build_button:
            return {
                "kind": PlayerActionKind.ClearTurretToBuild,
            }
        case gui_elements.game_over_main_menu_button:
            return {
                "kind": PlayerActionKind.ExitGame,
            }


def get_closest_enemy(
    world: esper.World,
    src_bbox: BoundingBox,
    *,
    range: float,
    exclude: list[int] = None,
) -> int | None:
    exclude = exclude or []

    ## find closest enemy
    closest_enemy = None
    closest_enemy_distance = float("inf")

    for enemy_ent, (
        _enemy,
        other_bbox,
    ) in world.get_components(Enemy, BoundingBox):
        if enemy_ent in exclude:
            continue

        distance_to_enemy = Vector2(other_bbox.rect.center).distance_to(
            Vector2(src_bbox.rect.center)
        )

        if distance_to_enemy <= range and distance_to_enemy < closest_enemy_distance:
            closest_enemy_distance = distance_to_enemy
            closest_enemy = enemy_ent

    return closest_enemy


def get_enemies_in_range(
    world: esper.World,
    src_bbox: BoundingBox,
    *,
    range: float,
    exclude: list[int] = None,
) -> list[int]:
    exclude = exclude or []

    ents_in_range = []

    for enemy_ent, (
        _enemy,
        other_bbox,
    ) in world.get_components(Enemy, BoundingBox):
        if enemy_ent in exclude:
            continue

        distance_to_enemy = Vector2(other_bbox.rect.center).distance_to(
            Vector2(src_bbox.rect.center)
        )

        if distance_to_enemy <= range:
            ents_in_range.append(enemy_ent)

    return ents_in_range


def unit_pathing_to_path_graph(unit_pathing: UnitPathing) -> PathGraph:
    """
    for dynamic spawns, copy the remaining points on the path
    """

    return PathGraph(
        vertices=[vert.copy() for vert in unit_pathing.vertices[unit_pathing.index :]]
    )
