from typing import NotRequired, TypedDict

from .enums import EnemyKind, PlayerActionKind, SpawningWaveStepKind, TurretKind


class PlayerAction(TypedDict):
    kind: PlayerActionKind

    ent: NotRequired[int]
    turret_kind: NotRequired[TurretKind]


class SpawningWaveStep(TypedDict):
    kind: SpawningWaveStepKind

    enemy_kind: NotRequired[EnemyKind]
    duration: NotRequired[float]
