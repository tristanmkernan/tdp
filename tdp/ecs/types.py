from typing import NotRequired, TypedDict

from .enums import (
    EnemyKind,
    PlayerActionKind,
    ResearchKind,
    SpawningWaveStepKind,
    TurretKind,
    TurretUpgradeablePropertyKind,
)


class PlayerAction(TypedDict):
    kind: PlayerActionKind

    ent: NotRequired[int]
    turret_kind: NotRequired[TurretKind]
    turret_property: NotRequired[TurretUpgradeablePropertyKind]
    research_kind: NotRequired[ResearchKind]


class SpawningWaveStep(TypedDict):
    kind: SpawningWaveStepKind

    enemy_kind: NotRequired[EnemyKind]
    duration: NotRequired[float]
