import enum


class CollidableKind(enum.IntEnum):
    Circle = enum.auto()
    Triangle = enum.auto()


class ScoreEventKind(enum.IntEnum):
    EnemyKill = enum.auto()
    EnemyDespawn = enum.auto()
    Time = enum.auto()


class InputEventKind(enum.IntEnum):
    KeyUp = enum.auto()
    KeyDown = enum.auto()
    MouseLeftClickUp = enum.auto()
    MouseLeftClickDown = enum.auto()


class PlayerActionKind(enum.IntEnum):
    SelectTurretBuildZone = enum.auto()


class RenderableKind(enum.IntEnum):
    Circle = enum.auto()
    Triangle = enum.auto()


class RenderableOrder(enum.IntEnum):
    Base = enum.auto()
    Environment = enum.auto()
    Objects = enum.auto()


class ObjectKind(enum.StrEnum):
    TurretBuildZone = "TurretBuildZone"
    Path = "Path"
