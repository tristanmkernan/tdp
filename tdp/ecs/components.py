import dataclasses

from pygame import Rect, Vector2, Surface

from .enums import RenderableOrder, ScoreEventKind


class Enemy:
    pass


@dataclasses.dataclass
class Spawning:
    rate: float = 0.0
    elapsed: float = 0.0

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
class Bullet:
    pass


@dataclasses.dataclass
class ScoreTracker:
    scores: dict[ScoreEventKind, int] = dataclasses.field(
        default_factory=lambda: {kind: 0 for kind in ScoreEventKind}
    )
    recent_events: list[ScoreEventKind] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class PlayerKeyInput:
    keydowns: set[int] = dataclasses.field(default_factory=set)


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
    rotation: Vector2 = dataclasses.field(default_factory=Vector2)


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
class Firing:
    elapsed: float = 0.0
    rate: float = 0.0

    @property
    def every(self):
        """
        How many seconds delay between firing
        """
        return 1.0 / self.rate
