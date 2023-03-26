from .components import PlayerResources
from .enums import TurretKind
from . import esper


TURRET_BUILD_COSTS: dict[TurretKind, int] = {
    TurretKind.Bullet: 50,
    TurretKind.Flame: 100,
    TurretKind.Rocket: 100,
}


def player_has_resources_to_build_turret(
    world: esper.World, turret_kind: TurretKind
) -> bool:
    player_resources = world.get_component(PlayerResources)[0][1]

    return player_resources.money >= TURRET_BUILD_COSTS[turret_kind]


def subtract_resources_to_build_turret(
    world: esper.World, turret_kind: TurretKind
) -> None:
    player_resources = world.get_component(PlayerResources)[0][1]

    player_resources.money -= TURRET_BUILD_COSTS[turret_kind]
