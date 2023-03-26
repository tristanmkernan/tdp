import enum


class ScoreEventKind(enum.IntEnum):
    EnemyKill = enum.auto()
    EnemyDespawn = enum.auto()
    Time = enum.auto()


class InputEventKind(enum.IntEnum):
    KeyUp = enum.auto()
    KeyDown = enum.auto()
    MouseLeftClickUp = enum.auto()
    MouseLeftClickDown = enum.auto()

    UIButtonPress = enum.auto()


class PlayerActionKind(enum.IntEnum):
    SelectTurretBuildZone = enum.auto()

    SetTurretToBuild = enum.auto()
    ClearTurretToBuild = enum.auto()


class RenderableOrder(enum.IntEnum):
    Base = enum.auto()
    Environment = enum.auto()
    Objects = enum.auto()


class ObjectKind(enum.StrEnum):
    TurretBuildZone = "TurretBuildZone"
    Path = "Path"


class TurretState(enum.IntEnum):
    Idle = enum.auto()
    Tracking = enum.auto()
    Firing = enum.auto()
    # TODO animation should not be part of the turret state
    FiringAnimation = enum.auto()
    Reloading = enum.auto()


class EnemyKind(enum.IntEnum):
    Grunt = enum.auto()
    Tank = enum.auto()


class TurretKind(enum.IntEnum):
    Bullet = enum.auto()
    Flame = enum.auto()
    Rocket = enum.auto()


class PlayerInputState(enum.IntEnum):
    Idle = enum.auto()
    BuildingTurret = enum.auto()


class SpawningWaveStepKind(enum.IntEnum):
    SpawnEnemy = enum.auto()
    Wait = enum.auto()
