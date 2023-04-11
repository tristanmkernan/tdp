import tomllib

from typing import Literal, TypedDict

from .enums import EnemyKind, ResearchKind, TurretKind, TurretUpgradeablePropertyKind


class EnemyStats(TypedDict):
    base_health: int
    health_per_level: int
    base_bounty: int
    bounty_per_level: int


class TurretStats(TypedDict):
    base: dict[TurretUpgradeablePropertyKind, int | float]
    per_level: dict[TurretUpgradeablePropertyKind, int | float]
    costs: dict[Literal["build"] | Literal["upgrade"], int]


class ResearchStats(TypedDict):
    durations: dict[ResearchKind, float]
    costs: dict[ResearchKind, int]


class StatsRepo(TypedDict):
    enemies: dict[EnemyKind, EnemyStats]
    turrets: dict[TurretKind, TurretStats]
    research: ResearchStats


def load_stats_repo() -> StatsRepo:
    with open("assets/statsrepo.toml", "rb") as f:
        stats_repo = tomllib.load(f)

    return stats_repo
