from .components import BoundingBox, TurretBuildZone
from .types import PlayerAction
from .enums import PlayerActionKind

from . import esper


def get_player_action_for_click(world: esper.World, pos) -> PlayerAction | None:
    # for now, just look for selecting turret build zones
    for ent, (bbox, bz) in world.get_components(BoundingBox, TurretBuildZone):
        if bbox.rect.collidepoint(pos):
            return {"kind": PlayerActionKind.SelectTurretBuildZone, "ent": ent}

    return None
