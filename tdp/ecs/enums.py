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
    SellTurret = enum.auto()

    StartResearch = enum.auto()

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


class EnemyKind(enum.StrEnum):
    Grunt = "grunt"
    Elite = "elite"
    Commando = "commando"
    Tank = "tank"


class TurretKind(enum.StrEnum):
    Bullet = "bullet"
    Flame = "flame"
    Rocket = "rocket"
    Frost = "frost"
    Lightning = "lightning"
    Poison = "poison"
    Tornado = "tornado"


enabled_turret_kinds = [
    TurretKind.Bullet,
    TurretKind.Flame,
    TurretKind.Rocket,
    TurretKind.Lightning,
    TurretKind.Poison,
    TurretKind.Tornado,
]


class TurretUpgradeablePropertyKind(enum.StrEnum):
    Damage = "damage"
    RateOfFire = "freq"
    Range = "range"

    DOTTickRate = "dot_tick_rate"
    DOTDuration = "dot_duration"


class PlayerInputState(enum.IntEnum):
    GameOver = enum.auto()
    Idle = enum.auto()
    BuildingTurret = enum.auto()
    SelectingTurret = enum.auto()


class SpawningWaveStepKind(enum.IntEnum):
    SpawnEnemy = enum.auto()
    Wait = enum.auto()


class VelocityAdjustmentSource(enum.IntEnum):
    Buffeted = enum.auto()


class VelocityAdjustmentKind(enum.IntEnum):
    Immobile = enum.auto()
    Slowdown = enum.auto()


class DamagesEnemyOnCollisionBehavior(enum.IntEnum):
    DeleteEntity = enum.auto()
    RemoveComponent = enum.auto()
    DoNothing = enum.auto()
    Pierce = enum.auto()


class DamagesEnemyEffectKind(enum.IntEnum):
    AddsComponent = enum.auto()
    DynamicCreator = enum.auto()


class ResearchKind(enum.StrEnum):
    UnlockFlameTurret = "unlock_flame_turret"
    UnlockRocketTurret = "unlock_rocket_turret"
    UnlockLightningTurret = "unlock_lightning_turret"
    UnlockPoisonTurret = "unlock_poison_turret"
    UnlockTornadoTurret = "unlock_tornado_turret"
    UnlockExtendedUpgrades = "unlock_extended_upgrades"
