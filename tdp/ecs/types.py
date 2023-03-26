from typing import NotRequired, TypedDict

from .enums import PlayerActionKind, TurretKind


class PlayerAction(TypedDict):
    kind: PlayerActionKind

    ent: NotRequired[int]
    turret_kind: NotRequired[TurretKind]
