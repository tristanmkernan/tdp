from tdp.ecs.statsrepo import StatsRepo
from .components import PlayerResources
from .enums import ResearchKind, TurretKind, TurretUpgradeablePropertyKind
from . import esper


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
    ResearchKind.UnlockFlameTurret: "Flame Turret",
    ResearchKind.UnlockRocketTurret: "Rocket Turret",
    ResearchKind.UnlockLightningTurret: "Lightning Turret",
    ResearchKind.UnlockPoisonTurret: "Poison Turret",
    ResearchKind.UnlockTornadoTurret: "Tornado Turret",
    ResearchKind.UnlockExtendedUpgrades: "Higher Upgrades",
}


TURRET_TO_RESEARCH: dict[TurretKind, ResearchKind] = {
    TurretKind.Flame: ResearchKind.UnlockFlameTurret,
    TurretKind.Rocket: ResearchKind.UnlockRocketTurret,
    TurretKind.Lightning: ResearchKind.UnlockLightningTurret,
    TurretKind.Poison: ResearchKind.UnlockPoisonTurret,
    TurretKind.Tornado: ResearchKind.UnlockTornadoTurret,
}

RESEARCH_TO_TURRET = {v: k for k, v in TURRET_TO_RESEARCH.items()}


def player_has_resources_to_build_turret(
    world: esper.World, turret_kind: TurretKind, stats_repo: StatsRepo
) -> bool:
    player_resources = world.get_component(PlayerResources)[0][1]

    return (
        player_resources.money >= stats_repo["turrets"][turret_kind]["costs"]["build"]
    )


def subtract_resources_to_build_turret(
    world: esper.World, turret_kind: TurretKind, stats_repo: StatsRepo
) -> None:
    player_resources = world.get_component(PlayerResources)[0][1]

    player_resources.money -= stats_repo["turrets"][turret_kind]["costs"]["build"]


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
    world: esper.World, player: int, research_kind: ResearchKind, stats_repo: StatsRepo
) -> bool:
    player_resources = world.component_for_entity(player, PlayerResources)

    return player_resources.money >= stats_repo["research"]["costs"][research_kind]


def subtract_resources_to_research(
    world: esper.World, player: int, research_kind: ResearchKind, stats_repo: StatsRepo
) -> None:
    player_resources = world.component_for_entity(player, PlayerResources)

    player_resources.money -= stats_repo["research"]["costs"][research_kind]
