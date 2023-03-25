import logging

import pygame

from pygame import Rect, Vector2

from ..constants import PLAYER_STARTING_MONEY

from .assets import Assets
from .components import (
    BoundingBox,
    Bullet,
    Despawnable,
    Enemy,
    PathGraph,
    PlayerKeyInput,
    PlayerResources,
    ScoreTracker,
    TurretMachine,
    UnitPathing,
    Velocity,
    Renderable,
)
from .enums import (
    RenderableOrder,
    ScoreEventKind,
    TurretState,
)

from . import esper

logger = logging.getLogger(__name__)


def create_scoreboard(world: esper.World):
    scoreboard = world.create_entity()

    world.add_component(scoreboard, ScoreTracker())


def spawn_tank(world: esper.World, spawn_point: int, *, assets: Assets):
    return spawn_enemy(world, spawn_point, assets.tank)


def spawn_grunt(world: esper.World, spawn_point: int, *, assets: Assets):
    return spawn_enemy(world, spawn_point, assets.grunt)


def spawn_enemy(world: esper.World, spawn_point: int, image: pygame.Surface):
    spawn_bbox = world.component_for_entity(spawn_point, BoundingBox)
    spawn_path_graph = world.component_for_entity(spawn_point, PathGraph)

    image_rect = image.get_rect()

    return world.create_entity(
        Enemy(bounty=10),
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


def kill_enemy(world: esper.World, enemy_ent: int):
    # remove enemy entity
    world.delete_entity(enemy_ent)

    # increase player resources by enemy bounty
    enemy = world.component_for_entity(enemy_ent, Enemy)
    player_resources = world.get_component(PlayerResources)[0][1]

    player_resources.money += enemy.bounty


def create_turret(world: esper.World, build_zone_ent: int, *, assets: Assets):
    bz_bbox = world.component_for_entity(build_zone_ent, BoundingBox)

    image = assets.turret
    image_rect = image.get_rect()

    bbox = BoundingBox(rect=Rect(image_rect))
    bbox.rect.center = bz_bbox.rect.center

    # for now, remove build zone entity, but may want to disable instead
    world.delete_entity(build_zone_ent)

    return world.create_entity(
        TurretMachine(state=TurretState.Idle),
        bbox,
        Renderable(image=image, order=RenderableOrder.Objects),
    )


def create_bullet(world: esper.World, turret_ent: int, enemy_ent: int):
    turret_bbox = world.component_for_entity(turret_ent, BoundingBox)
    enemy_bbox = world.component_for_entity(enemy_ent, BoundingBox)

    vec = (
        Vector2(enemy_bbox.rect.center) - Vector2(turret_bbox.rect.center)
    ).normalize()
    vec.scale_to_length(1.25)

    return world.create_entity(
        # TODO bullet params
        BoundingBox(rect=Rect(turret_bbox.rect.x, turret_bbox.rect.y, 12, 12)),
        #        Renderable(),
        Bullet(),
        Velocity(vec=vec),
    )


def create_player_input(world: esper.World):
    player_input = world.create_entity()

    world.add_component(player_input, PlayerKeyInput())


def create_player_resources(world: esper.World):
    return world.create_entity(PlayerResources(money=PLAYER_STARTING_MONEY))


def track_score_event(world: esper.World, kind: ScoreEventKind):
    _, score_tracker = world.get_component(ScoreTracker)[0]

    score_tracker.recent_events.insert(0, kind)
    score_tracker.recent_events = score_tracker.recent_events[:10]

    score_tracker.scores[kind] += 1
