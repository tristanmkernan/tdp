from typing import NotRequired, TypedDict

from .enums import PlayerActionKind


class PlayerAction(TypedDict):
    kind: PlayerActionKind
    ent: NotRequired[int]
