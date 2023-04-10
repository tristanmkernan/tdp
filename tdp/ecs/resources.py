from .components import PlayerResources
from .enums import ResearchKind, TurretKind, TurretUpgradeablePropertyKind
from . import esper


TURRET_BUILD_COSTS: dict[TurretKind, int] = {
    TurretKind.Bullet: 50,
    TurretKind.Flame: 250,
    TurretKind.Frost: 100,
    TurretKind.Rocket: 500,
    TurretKind.Lightning: 1000,
    TurretKind.Poison: 1000,
    TurretKind.Tornado: 1000,
}

TURRET_NAMES: dict[TurretKind, str] = {
    TurretKind.Bullet: "Bullet",
    TurretKind.Flame: "Flame",
    TurretKind.Frost: "Frost",
    TurretKind.Rocket: "Rocket",
    TurretKind.Lightning: "Lightning",
    TurretKind.Poison: "Poison",
    TurretKind.Tornado: "Tornado",
}

TURRET_UPGRADE_NAMES: dict[TurretUpgradeablePropertyKind, str] = {
    TurretUpgradeablePropertyKind.Damage: "Damage",
    TurretUpgradeablePropertyKind.Range: "Range",
    TurretUpgradeablePropertyKind.RateOfFire: "Freq",
}

TURRET_UPGRADE_COSTS: dict[TurretUpgradeablePropertyKind, int] = {
    TurretUpgradeablePropertyKind.Damage: 25,
    TurretUpgradeablePropertyKind.Range: 25,
    TurretUpgradeablePropertyKind.RateOfFire: 25,
}

TURRET_SELL_REWARD = 25


RESEARCH_NAMES: dict[ResearchKind, str] = {
    ResearchKind.UnlockFlameThrowerTurret: "Flame Turret",
    ResearchKind.UnlockRocketTurret: "Rocket Turret",
    ResearchKind.UnlockLightningTurret: "Lightning Turret",
    ResearchKind.UnlockPoisonTurret: "Poison Turret",
    ResearchKind.UnlockTornadoTurret: "Tornado Turret",
    ResearchKind.UnlockExtendedUpgrades: "Higher Upgrades",
}

RESEARCH_COSTS: dict[ResearchKind, int] = {
    ResearchKind.UnlockFlameThrowerTurret: 250,
    ResearchKind.UnlockRocketTurret: 250,
    ResearchKind.UnlockLightningTurret: 1000,
    ResearchKind.UnlockPoisonTurret: 1000,
    ResearchKind.UnlockTornadoTurret: 1000,
    ResearchKind.UnlockExtendedUpgrades: 1000,
}

RESEARCH_DURATIONS: dict[ResearchKind, int] = {
    ResearchKind.UnlockFlameThrowerTurret: 10 * 1_000,
    ResearchKind.UnlockRocketTurret: 10 * 1_000,
    ResearchKind.UnlockLightningTurret: 30 * 1_000,
    ResearchKind.UnlockPoisonTurret: 30 * 1_000,
    ResearchKind.UnlockTornadoTurret: 30 * 1_000,
    ResearchKind.UnlockExtendedUpgrades: 30 * 1_000,
}

TURRET_TO_RESEARCH: dict[TurretKind, ResearchKind] = {
    TurretKind.Flame: ResearchKind.UnlockFlameThrowerTurret,
    TurretKind.Rocket: ResearchKind.UnlockRocketTurret,
    TurretKind.Lightning: ResearchKind.UnlockLightningTurret,
    TurretKind.Poison: ResearchKind.UnlockPoisonTurret,
    TurretKind.Tornado: ResearchKind.UnlockTornadoTurret,
}

RESEARCH_TO_TURRET = {v: k for k, v in TURRET_TO_RESEARCH.items()}


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


def add_resources_from_turret_sale(world: esper.World, turret_ent: int):
    player_resources = world.get_component(PlayerResources)[0][1]

    player_resources.money += TURRET_SELL_REWARD


def player_has_resources_to_research(
    world: esper.World, player: int, research_kind: ResearchKind
) -> bool:
    player_resources = world.component_for_entity(player, PlayerResources)

    return player_resources.money >= RESEARCH_COSTS[research_kind]


def subtract_resources_to_research(
    world: esper.World, player: int, research_kind: ResearchKind
) -> None:
    player_resources = world.component_for_entity(player, PlayerResources)

    player_resources.money -= RESEARCH_COSTS[research_kind]
