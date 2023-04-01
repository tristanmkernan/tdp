import logging

from pygame.math import Vector2

from tdp.ecs.gui import GuiElements

from .components import BoundingBox, TurretBuildZone, Enemy, TurretMachine
from .types import PlayerAction
from .enums import PlayerActionKind, TurretKind, TurretUpgradeablePropertyKind

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
    match ui_element:
        case gui_elements.basic_turret_build_button:
            return {
                "kind": PlayerActionKind.SetTurretToBuild,
                "turret_kind": TurretKind.Bullet,
            }
        case gui_elements.flame_turret_build_button:
            return {
                "kind": PlayerActionKind.SetTurretToBuild,
                "turret_kind": TurretKind.Flame,
            }
        case gui_elements.frost_turret_build_button:
            return {
                "kind": PlayerActionKind.SetTurretToBuild,
                "turret_kind": TurretKind.Frost,
            }
        case gui_elements.rocket_turret_build_button:
            return {
                "kind": PlayerActionKind.SetTurretToBuild,
                "turret_kind": TurretKind.Rocket,
            }
        case gui_elements.clear_turret_build_button:
            return {
                "kind": PlayerActionKind.ClearTurretToBuild,
            }
        case gui_elements.selected_turret_damage_upgrade_button:
            return {
                "kind": PlayerActionKind.UpgradeTurretProperty,
                "turret_property": TurretUpgradeablePropertyKind.Damage,
            }
        case gui_elements.selected_turret_rate_of_fire_upgrade_button:
            return {
                "kind": PlayerActionKind.UpgradeTurretProperty,
                "turret_property": TurretUpgradeablePropertyKind.RateOfFire,
            }
        case gui_elements.selected_turret_range_upgrade_button:
            return {
                "kind": PlayerActionKind.UpgradeTurretProperty,
                "turret_property": TurretUpgradeablePropertyKind.Range,
            }


def get_closest_enemy(
    world: esper.World, turret_bbox: BoundingBox, *, range: float
) -> int | None:
    ## find closest enemy
    closest_enemy = None
    closest_enemy_distance = float("inf")

    for enemy_ent, (
        _enemy,
        other_bbox,
    ) in world.get_components(Enemy, BoundingBox):
        distance_to_enemy = Vector2(other_bbox.rect.center).distance_to(
            Vector2(turret_bbox.rect.center)
        )

        if distance_to_enemy <= range and distance_to_enemy < closest_enemy_distance:
            closest_enemy_distance = distance_to_enemy
            closest_enemy = enemy_ent

    return closest_enemy
