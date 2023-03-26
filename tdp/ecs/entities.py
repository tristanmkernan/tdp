import logging
import random

import pygame

from pygame import Rect, Vector2

from ..constants import PLAYER_STARTING_MONEY

from .assets import Assets
from .components import (
    BoundingBox,
    DamagesEnemy,
    Despawnable,
    Enemy,
    PathGraph,
    PlayerInputMachine,
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
    TurretKind,
    TurretState,
)

from . import esper

logger = logging.getLogger(__name__)


def create_scoreboard(world: esper.World):
    scoreboard = world.create_entity()

    world.add_component(scoreboard, ScoreTracker())


def spawn_tank(world: esper.World, spawn_point: int, *, assets: Assets):
    return spawn_enemy(world, spawn_point, assets.tank, bounty=25, max_health=10)


def spawn_grunt(world: esper.World, spawn_point: int, *, assets: Assets):
    return spawn_enemy(world, spawn_point, assets.grunt, bounty=5, max_health=2)


def spawn_enemy(
    world: esper.World,
    spawn_point: int,
    image: pygame.Surface,
    bounty: int,
    max_health: int,
):
    spawn_bbox = world.component_for_entity(spawn_point, BoundingBox)
    spawn_path_graph = world.component_for_entity(spawn_point, PathGraph)

    image_rect = image.get_rect()

    return world.create_entity(
        Enemy(bounty=bounty, max_health=max_health),
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


def create_flame_turret(world: esper.World, build_zone_ent: int, *, assets: Assets):
    bz_bbox = world.component_for_entity(build_zone_ent, BoundingBox)

    image = assets.flame_turret
    image_rect = image.get_rect()

    bbox = BoundingBox(rect=Rect(image_rect))
    bbox.rect.center = bz_bbox.rect.center

    # for now, remove build zone entity, but may want to disable instead
    world.delete_entity(build_zone_ent)

    return world.create_entity(
        TurretMachine(
            state=TurretState.Idle,
            kind=TurretKind.Flame,
            firing_cooldown=5.0,
            firing_animation_duration=0,
            range=250,
        ),
        bbox,
        Renderable(image=image, order=RenderableOrder.Objects),
    )


def create_bullet_turret(world: esper.World, build_zone_ent: int, *, assets: Assets):
    bz_bbox = world.component_for_entity(build_zone_ent, BoundingBox)

    image = assets.bullet_turret
    image_rect = image.get_rect()

    bbox = BoundingBox(rect=Rect(image_rect))
    bbox.rect.center = bz_bbox.rect.center

    # for now, remove build zone entity, but may want to disable instead
    world.delete_entity(build_zone_ent)

    return world.create_entity(
        TurretMachine(state=TurretState.Idle, kind=TurretKind.Bullet),
        bbox,
        Renderable(image=image, order=RenderableOrder.Objects),
    )


def fire_turret(
    world: esper.World,
    turret_ent: int,
    turret_machine: TurretMachine,
    enemy_ent: int,
    *,
    assets: Assets,
):
    match turret_machine.kind:
        case TurretKind.Bullet:
            create_bullet(world, turret_ent, enemy_ent)

        case TurretKind.Flame:
            create_flame(world, turret_ent, enemy_ent, assets=assets)


def create_flame(
    world: esper.World, turret_ent: int, enemy_ent: int, *, assets: Assets
):
    turret_bbox = world.component_for_entity(turret_ent, BoundingBox)
    enemy_bbox = world.component_for_entity(enemy_ent, BoundingBox)

    image = assets.flame_particle
    image_rect = image.get_rect()

    vec = (
        Vector2(enemy_bbox.rect.center) - Vector2(turret_bbox.rect.center)
    ).normalize()

    # introduce random rotation, flame turret creates "cone" of flame
    # +15, -15 deg range (30 deg total cone)
    vec = vec.rotate(random.uniform(-15.0, 15.0))

    vec.scale_to_length(0.35)

    # flame should spawn outside turret, not inside
    # let's adjust position along target vector
    turret_pos_offset = vec.copy()
    turret_pos_offset.scale_to_length(64)

    flame_center = Vector2(turret_bbox.rect.center) + turret_pos_offset

    flame_rect = Rect((0, 0), image_rect.size)
    flame_rect.center = (flame_center.x, flame_center.y)

    return world.create_entity(
        # TODO flames should spawn from outside turret, not inside
        BoundingBox(rect=flame_rect, rotation=vec),
        DamagesEnemy(damage=1),
        Renderable(image=image, order=RenderableOrder.Objects),
        Velocity(vec=vec),
    )


def create_bullet(world: esper.World, turret_ent: int, enemy_ent: int):
    turret_bbox = world.component_for_entity(turret_ent, BoundingBox)
    enemy_bbox = world.component_for_entity(enemy_ent, BoundingBox)

    bullet_size = 12, 12

    # spawn bullet on top of enemy, "instantaneous" damage

    return world.create_entity(
        BoundingBox(rect=Rect(enemy_bbox.rect.center, bullet_size)),
        DamagesEnemy(damage=1),
    )


def create_player_input(world: esper.World):
    player_input = world.create_entity()

    world.add_component(player_input, PlayerInputMachine())


def create_player_resources(world: esper.World):
    return world.create_entity(PlayerResources(money=PLAYER_STARTING_MONEY))


def track_score_event(world: esper.World, kind: ScoreEventKind):
    _, score_tracker = world.get_component(ScoreTracker)[0]

    score_tracker.recent_events.insert(0, kind)
    score_tracker.recent_events = score_tracker.recent_events[:10]

    score_tracker.scores[kind] += 1
