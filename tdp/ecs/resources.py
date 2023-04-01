from .components import PlayerResources
from .enums import TurretKind, TurretUpgradeablePropertyKind
from . import esper


TURRET_BUILD_COSTS: dict[TurretKind, int] = {
    TurretKind.Bullet: 50,
    TurretKind.Flame: 100,
    TurretKind.Frost: 100,
    TurretKind.Rocket: 100,
}

TURRET_NAMES: dict[TurretKind, str] = {
    TurretKind.Bullet: "Bullet",
    TurretKind.Flame: "Flame",
    TurretKind.Frost: "Frost",
    TurretKind.Rocket: "Rocket",
}

TURRET_UPGRADE_COSTS: dict[TurretUpgradeablePropertyKind, int] = {
    TurretUpgradeablePropertyKind.Damage: 25,
    TurretUpgradeablePropertyKind.Range: 25,
    TurretUpgradeablePropertyKind.RateOfFire: 25,
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


def player_has_resources_to_upgrade_turret(
    world: esper.World, turret_property: TurretUpgradeablePropertyKind
) -> bool:
    player_resources = world.get_component(PlayerResources)[0][1]

    return player_resources.money >= TURRET_UPGRADE_COSTS[turret_property]


def subtract_resources_to_upgrade_turret(
    world: esper.World, turret_property: TurretUpgradeablePropertyKind
) -> None:
    player_resources = world.get_component(PlayerResources)[0][1]

    player_resources.money -= TURRET_UPGRADE_COSTS[turret_property]
