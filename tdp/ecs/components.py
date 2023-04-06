from collections import defaultdict
from typing import Any, Protocol

import dataclasses

from pygame import Rect, Vector2, Surface

from .assets import Assets
from .enums import (
    DamagesEnemyOnCollisionBehavior,
    RenderableExtraKind,
    RenderableExtraOrder,
    RenderableOrder,
    ScoreEventKind,
    TurretState,
    TurretKind,
    PlayerInputState,
    TurretUpgradeablePropertyKind,
    VelocityAdjustmentKind,
    DamagesEnemyEffectKind,
    VelocityAdjustmentSource,
)
from .types import SpawningWaveStep

from . import esper


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
    wave: list[SpawningWaveStep]
    total_enemy_spawns: int

    enemy_spawn_count: int = 0
    current_index: int = 0

    elapsed: float = 0.0

    def advance(self):
        self.current_index += 1
        self.elapsed = 0.0

    @property
    def current_step(self):
        return self.wave[self.current_index]

    @property
    def over(self):
        return self.current_index >= len(self.wave)

    @property
    def progress(self):
        return int(100.0 * self.enemy_spawn_count / self.total_enemy_spawns)


@dataclasses.dataclass
class Spawning:
    waves: list[SpawningWave]
    current_wave_index: int = 0

    def advance(self):
        self.current_wave_index += 1

    @property
    def current_wave(self):
        return self.waves[self.current_wave_index]

    @property
    def current_wave_num(self):
        return self.current_wave_index + 1


class Despawning:
    pass


class Despawnable:
    pass


@dataclasses.dataclass
class VelocityAdjustment:
    kind: VelocityAdjustmentKind

    duration: float

    elapsed: float = 0.0

    factor: float = 0.0

    # TODO this should be a mixin, often repeated
    @property
    def expired(self):
        return self.elapsed >= self.duration


@dataclasses.dataclass
class Velocity:
    vec: Vector2 = dataclasses.field(default_factory=Vector2)
    adjustments: dict[VelocityAdjustmentSource, VelocityAdjustment] = dataclasses.field(
        default_factory=dict
    )


class DamagesEnemyDynamicEffectCreator(Protocol):
    def __call__(
        self, world: esper.World, source_ent: int, enemy_ent: int, *, assets: Assets
    ) -> Any:
        ...


@dataclasses.dataclass
class DamagesEnemyEffect:
    kind: DamagesEnemyEffectKind

    component: Any | None = None
    overwrite: bool = True

    dynamic_effect_creator: DamagesEnemyDynamicEffectCreator | None = None


@dataclasses.dataclass
class DamagesEnemy:
    damage: int

    on_collision_behavior: DamagesEnemyOnCollisionBehavior = (
        DamagesEnemyOnCollisionBehavior.DeleteEntity
    )

    # how many enemies this entity can damage before being removed
    pierces: int = 1
    pierced_count: int = 0

    effects: list[DamagesEnemyEffect] = dataclasses.field(default_factory=list)

    @property
    def expired(self):
        return self.pierced_count >= self.pierces

    @property
    def applies_effects(self):
        return bool(self.effects)


@dataclasses.dataclass
class ScoreTracker:
    scores: dict[ScoreEventKind, int] = dataclasses.field(
        default_factory=lambda: defaultdict(int)
    )

    @property
    def total_score(self):
        return self.scores[ScoreEventKind.EnemyKill]


@dataclasses.dataclass
class PlayerInputMachine:
    state: PlayerInputState = PlayerInputState.Idle

    turret_to_build: TurretKind | None = None
    selected_turret: int | None = None


@dataclasses.dataclass
class RenderableExtra:
    image: Surface
    rect: Rect
    order: RenderableExtraOrder


def empty_extra_renderable_generator():
    return RenderableExtra(
        image=Surface((0, 0)),
        rect=Rect(0, 0, 0, 0),
        order=RenderableExtraOrder.Over,
    )


@dataclasses.dataclass
class Renderable:
    image: Surface
    order: RenderableOrder

    extras: dict[RenderableExtraKind, RenderableExtra] = dataclasses.field(
        default_factory=lambda: defaultdict(empty_extra_renderable_generator)
    )

    original_image: Surface = dataclasses.field(init=False)

    def __post_init__(self):
        self.original_image = self.image

    @property
    def composite(self):
        return bool(self.extras)


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
    upgrade_levels: dict[TurretUpgradeablePropertyKind, int]
    base_stats: dict[TurretUpgradeablePropertyKind, int | float]
    stat_changes_per_level: dict[TurretUpgradeablePropertyKind, int | float]

    rotates: bool = True

    elapsed: float = 0.0

    firing_animation_duration: float = 0.0
    reloading_duration: float = 0.0

    idle_rotation_speed: float = 0.025

    @property
    def can_fire(self):
        return self.elapsed >= self.firing_cooldown

    @property
    def finished_firing_animation(self):
        return self.elapsed >= self.firing_animation_duration

    @property
    def finished_reloading(self):
        return self.elapsed >= self.reloading_duration

    def _per_level_stat(self, kind: TurretUpgradeablePropertyKind):
        level = self.upgrade_levels[kind]
        base = self.base_stats[kind]
        per_level = self.stat_changes_per_level[kind]

        return base + level * per_level

    @property
    def firing_cooldown(self) -> float:
        return self._per_level_stat(TurretUpgradeablePropertyKind.RateOfFire)

    @property
    def damage(self) -> int:
        return self._per_level_stat(TurretUpgradeablePropertyKind.Damage)

    @property
    def range(self) -> float:
        return self._per_level_stat(TurretUpgradeablePropertyKind.Range)


@dataclasses.dataclass
class PlayerResources:
    money: int


@dataclasses.dataclass
class RocketMissile:
    damage: int


@dataclasses.dataclass
class FrostMissile:
    damage: int


class RemoveOnOutOfBounds:
    pass


@dataclasses.dataclass
class TimeToLive:
    elapsed: float = 0.0
    duration: float = 250.0

    @property
    def expired(self):
        return self.elapsed >= self.duration


@dataclasses.dataclass
class FadeOut:
    elapsed: float = 0.0
    duration: float = 250.0

    @property
    def alpha(self):
        """
        Percent complete
        """
        return max(0.0, self.elapsed / self.duration)


@dataclasses.dataclass
class Burning:
    damage: int
    damage_tick_rate: float

    duration: float

    ticks: int = 0
    elapsed: float = 0.0

    @property
    def tick_due(self):
        return self.elapsed >= (self.ticks + 1) * self.damage_tick_rate

    @property
    def expired(self):
        return self.elapsed >= self.duration

    def reapply(self, other: "Burning"):
        # dont want to interrupt damage ticks, want to extend duration
        self.duration = self.elapsed + other.duration


@dataclasses.dataclass
class Poisoned:
    damage: int
    damage_tick_rate: float

    duration: float

    ticks: int = 0
    elapsed: float = 0.0

    @property
    def tick_due(self):
        return self.elapsed >= (self.ticks + 1) * self.damage_tick_rate

    @property
    def expired(self):
        return self.elapsed >= self.duration

    def reapply(self, other: "Burning"):
        # dont want to interrupt damage ticks, want to extend duration
        self.duration = self.elapsed + other.duration


@dataclasses.dataclass
class Buffeted:
    damage: int
    damage_tick_rate: float

    duration: float

    ticks: int = 0
    elapsed: float = 0.0

    @property
    def tick_due(self):
        return self.elapsed >= (self.ticks + 1) * self.damage_tick_rate

    @property
    def expired(self):
        return self.elapsed >= self.duration

    def reapply(self, other: "Burning"):
        # dont want to interrupt damage ticks, want to extend duration
        self.duration = self.elapsed + other.duration


@dataclasses.dataclass
class Frozen:
    duration: float

    elapsed: float = 0.0

    @property
    def expired(self):
        return self.elapsed >= self.duration

    def reapply(self, other: "Frozen"):
        # dont want to interrupt damage ticks, want to extend duration
        self.duration = self.elapsed + other.duration


@dataclasses.dataclass
class Shocked:
    duration: float

    elapsed: float = 0.0

    @property
    def expired(self):
        return self.elapsed >= self.duration

    def reapply(self, other: "Frozen"):
        # dont want to interrupt damage ticks, want to extend duration
        self.duration = self.elapsed + other.duration


@dataclasses.dataclass
class Animated:
    frames: list[Surface]
    step: float

    elapsed: float = 0.0
    current_frame_index: int = 0

    @property
    def current_frame(self):
        return self.frames[self.current_frame_index]

    @property
    def frame_expired(self):
        return self.elapsed > self.step

    def advance_frame(self):
        self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
        self.elapsed = 0.0
