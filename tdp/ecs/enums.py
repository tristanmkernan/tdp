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
    SelectTurret = enum.auto()

    SetTurretToBuild = enum.auto()
    ClearTurretToBuild = enum.auto()

    UpgradeTurretProperty = enum.auto()

    ExitGame = enum.auto()


class RenderableExtraOrder(enum.IntEnum):
    Under = -1
    Over = 1


class RenderableExtraKind(enum.IntEnum):
    TurretBase = enum.auto()
    HealthBar = enum.auto()
    StatusEffectBar = enum.auto()
    TurretRange = enum.auto()


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
    Elite = enum.auto()
    Commando = enum.auto()
    Tank = enum.auto()


class TurretKind(enum.IntEnum):
    Bullet = enum.auto()
    Flame = enum.auto()
    Rocket = enum.auto()
    Frost = enum.auto()


class TurretUpgradeablePropertyKind(enum.IntEnum):
    Damage = enum.auto()
    RateOfFire = enum.auto()
    Range = enum.auto()


class PlayerInputState(enum.IntEnum):
    GameOver = enum.auto()
    Idle = enum.auto()
    BuildingTurret = enum.auto()
    SelectingTurret = enum.auto()


class SpawningWaveStepKind(enum.IntEnum):
    SpawnEnemy = enum.auto()
    Wait = enum.auto()


class VelocityAdjustmentKind(enum.IntEnum):
    Immobile = enum.auto()
    Slowdown = enum.auto()


class DamagesEnemyOnCollisionBehavior(enum.IntEnum):
    DeleteEntity = enum.auto()
    RemoveComponent = enum.auto()


class DamagesEnemyEffectKind(enum.IntEnum):
    AddsComponent = enum.auto()
    DynamicCreator = enum.auto()
