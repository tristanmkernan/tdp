import dataclasses

from pygame import Rect, Vector2, Surface

from .enums import (
    RenderableOrder,
    ScoreEventKind,
    TurretState,
    EnemyKind,
    TurretKind,
    PlayerInputState,
)


@dataclasses.dataclass
class Enemy:
    bounty: int

    max_health: int
    health: int = dataclasses.field(init=False)

    def take_damage(self, amount: int):
        self.health = max(self.health - amount, 0)

    @property
    def is_dead(self):
        return self.health == 0

    @property
    def health_ratio(self):
        return int(100.0 * self.health / self.max_health)

    def __post_init__(self):
        self.health = self.max_health


@dataclasses.dataclass
class SpawningWave:
    wave: list[EnemyKind]
    current_index: int = 0

    def get_and_advance(self):
        enemy_kind = self.wave[self.current_index]

        self.current_index += 1

        return enemy_kind

    @property
    def over(self):
        return self.current_index >= len(self.wave)

    @property
    def progress(self):
        return int(100.0 * self.current_index / len(self.wave))


@dataclasses.dataclass
class Spawning:
    waves: list[SpawningWave]
    current_wave_index: int = 0
    rate: float = 0.0
    elapsed: float = 0.0

    def advance(self):
        self.current_wave_index += 1

    @property
    def current_wave(self):
        return self.waves[self.current_wave_index]

    @property
    def current_wave_num(self):
        return self.current_wave_index + 1

    @property
    def every(self):
        """
        How many seconds delay between spawns
        """
        return 1.0 / self.rate


class Despawning:
    pass


class Despawnable:
    pass


@dataclasses.dataclass
class Velocity:
    vec: Vector2 = dataclasses.field(default_factory=Vector2)


@dataclasses.dataclass
class DamagesEnemy:
    damage: int


@dataclasses.dataclass
class ScoreTracker:
    scores: dict[ScoreEventKind, int] = dataclasses.field(
        default_factory=lambda: {kind: 0 for kind in ScoreEventKind}
    )
    recent_events: list[ScoreEventKind] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class PlayerInputMachine:
    state: PlayerInputState = PlayerInputState.Idle

    turret_to_build: TurretKind | None = None


@dataclasses.dataclass
class Renderable:
    image: Surface
    order: RenderableOrder

    original_image: Surface = dataclasses.field(init=False)

    def __post_init__(self):
        self.original_image = self.image


@dataclasses.dataclass
class Lifetime:
    remaining: float = 0.0


@dataclasses.dataclass
class BoundingBox:
    rect: Rect
    rotation: Vector2 = dataclasses.field(default_factory=lambda: Vector2(1, 0))


@dataclasses.dataclass
class PathGraph:
    vertices: list[Vector2] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class UnitPathing:
    vertices: list[Vector2] = dataclasses.field(default_factory=list)
    index: int = 0

    @property
    def current_target(self):
        return self.vertices[self.index]

    def advance(self):
        self.index = min(self.index + 1, len(self.vertices) - 1)


class TurretBuildZone:
    pass


@dataclasses.dataclass
class TurretMachine:
    state: TurretState
    kind: TurretKind

    firing_cooldown: float = 1_000.0
    firing_animation_duration: float = 250.0
    elapsed: float = 0.0
    idle_rotation_speed: float = 0.025
    range: float = 500.0

    @property
    def can_fire(self):
        return self.elapsed >= self.firing_cooldown

    @property
    def finished_firing_animation(self):
        return self.elapsed >= self.firing_animation_duration


@dataclasses.dataclass
class PlayerResources:
    money: int
