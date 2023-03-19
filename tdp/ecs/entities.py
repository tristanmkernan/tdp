import logging

import pygame

from pygame import Rect

from tdp.constants import SCREEN_HEIGHT, SCREEN_WIDTH

from .components import (
    BoundingBox,
    Bullet,
    Despawnable,
    Despawning,
    Enemy,
    PathGraph,
    PlayerKeyInput,
    ScoreTracker,
    UnitPathing,
    Velocity,
    Spawning,
    Renderable,
)
from .enums import CollidableKind, RenderableKind, RenderableOrder, ScoreEventKind

from . import esper

logger = logging.getLogger(__name__)


def create_scoreboard(world: esper.World):
    scoreboard = world.create_entity()

    world.add_component(scoreboard, ScoreTracker())


def spawn_enemy(world: esper.World, spawn_point: int):
    spawn_bbox = world.component_for_entity(spawn_point, BoundingBox)
    spawn_path_graph = world.component_for_entity(spawn_point, PathGraph)

    image = pygame.image.load("assets/enemies/grunt.png")
    image_rect = image.get_rect()

    return world.create_entity(
        Enemy(),
        Velocity(),
        BoundingBox(
            rect=Rect(
                spawn_bbox.rect.x,
                spawn_bbox.rect.y - image_rect.height / 2,
                image_rect.width,
                image_rect.height,
            )
        ),
        Renderable(order=RenderableOrder.Objects, image=image),
        Despawnable(),
        UnitPathing(vertices=spawn_path_graph.vertices),
    )


def create_player_ship(world: esper.World):
    player_ship = world.create_entity()

    world.add_component(player_ship, PlayerShip())
    world.add_component(player_ship, Position(x=SCREEN_WIDTH / 2, y=SCREEN_HEIGHT / 2))
    world.add_component(player_ship, Velocity(max=0.25))
    world.add_component(player_ship, Acceleration())
    world.add_component(player_ship, Rotation())
    world.add_component(
        player_ship,
        Collidable(
            kind=CollidableKind.Circle,
            radius=3,
        ),
    )
    world.add_component(
        player_ship, BulletAmmo(recharge_rate=1.0 / 500.0, count=3, max=5)
    )

    renderables = RenderableCollection(
        items=[
            Renderable(RenderableKind.Circle, radius=15, color=(255, 0, 0)),
            Renderable(
                RenderableKind.Circle,
                radius=5,
                color=(0, 255, 0),
                offset=PositionOffset(x=10),
            ),
        ]
    )
    world.add_component(player_ship, renderables)


def create_bullet(world: esper.World):
    player, (
        player_ship,
        player_position,
        player_velocity,
        bullet_ammo,
    ) = world.get_components(PlayerShip, Position, Velocity, BulletAmmo)[0]

    if bullet_ammo.empty:
        return

    # subtract one bullet
    bullet_ammo.count -= 1

    bullet = world.create_entity()

    offset = get_offset_for_rotation(player_position.rotation, magnitude=0.75)

    velocity = Velocity(x=offset.x, y=offset.y)

    world.add_component(bullet, Position(x=player_position.x, y=player_position.y))
    world.add_component(bullet, velocity)
    world.add_component(
        bullet, Renderable(kind=RenderableKind.Circle, radius=3, color=(0, 0, 0))
    )
    world.add_component(bullet, Collidable(radius=3, kind=CollidableKind.Circle))
    world.add_component(bullet, Bullet())

    return bullet


def create_player_input(world: esper.World):
    player_input = world.create_entity()

    world.add_component(player_input, PlayerKeyInput())


def track_score_event(world: esper.World, kind: ScoreEventKind):
    _, score_tracker = world.get_component(ScoreTracker)[0]

    score_tracker.recent_events.insert(0, kind)
    score_tracker.recent_events = score_tracker.recent_events[:10]

    score_tracker.scores[kind] += 1


# TODO could be part of difficulty increase over time
def increase_spawn_rate(world: esper.World, multiplier: float = 1.25):
    for _, spawning in world.get_component(Spawning):
        spawning.rate *= multiplier


def set_player_acceleration(
    world: esper.World, *, forward: bool = True, unset: bool = False
):
    _, (_, pos, acc) = world.get_components(PlayerShip, Position, Acceleration)[0]

    if unset:
        acc.x = acc.y = 0.0
    else:
        rotation = pos.rotation

        offset = get_offset_for_rotation(rotation, 0.5 / 1_000)

        acc.x = offset.x * (1 if forward else -1)
        acc.y = offset.y * (1 if forward else -1)


def set_player_rotating_right(world: esper.World, val: bool):
    _, (_, rot) = world.get_components(PlayerShip, Rotation)[0]

    if val:
        rot.speed = -1.0 / 500.0
    else:
        rot.speed = 0.0


def set_player_rotating_left(world: esper.World, val: bool):
    _, (_, rot) = world.get_components(PlayerShip, Rotation)[0]

    if val:
        rot.speed = 1.0 / 500.0
    else:
        rot.speed = 0.0
