from pygame.math import Vector2

from .components import BoundingBox, TurretBuildZone, Enemy
from .types import PlayerAction
from .enums import PlayerActionKind

from . import esper


def get_player_action_for_click(world: esper.World, pos) -> PlayerAction | None:
    # for now, just look for selecting turret build zones
    for ent, (bbox, bz) in world.get_components(BoundingBox, TurretBuildZone):
        if bbox.rect.collidepoint(pos):
            return {"kind": PlayerActionKind.SelectTurretBuildZone, "ent": ent}

    return None


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
