import logging
import random

import pygame

from pygame import Rect, Vector2

from ..constants import PLAYER_STARTING_MONEY

from .assets import Assets
from .components import (
    Animated,
    BoundingBox,
    Burning,
    DamagesEnemy,
    DamagesEnemyEffect,
    Despawnable,
    Enemy,
    PathGraph,
    PlayerInputMachine,
    PlayerResources,
    RenderableExtra,
    ScoreTracker,
    TurretMachine,
    UnitPathing,
    Velocity,
    Renderable,
    RocketMissile,
    RemoveOnOutOfBounds,
    TimeToLive,
    Frozen,
    FrostMissile,
)
from .enums import (
    DamagesEnemyEffectKind,
    DamagesEnemyOnCollisionBehavior,
    RenderableExtraKind,
    RenderableExtraOrder,
    RenderableOrder,
    ScoreEventKind,
    TurretKind,
    TurretState,
    TurretUpgradeablePropertyKind,
)

from . import esper

logger = logging.getLogger(__name__)


def create_scoreboard(world: esper.World):
    scoreboard = world.create_entity()

    world.add_component(scoreboard, ScoreTracker())


def spawn_tank(world: esper.World, spawn_point: int, *, assets: Assets):
    return spawn_enemy(world, spawn_point, assets.tank, bounty=25, max_health=10)


def spawn_grunt(world: esper.World, spawn_point: int, *, assets: Assets):
    return spawn_enemy(world, spawn_point, assets.grunt, bounty=5, max_health=5)


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
        Renderable(
            order=RenderableOrder.Objects,
            image=image,
            # not a huge fan that this is initialized like this
            extras={
                RenderableExtraKind.StatusEffectBar: RenderableExtra(
                    image=pygame.Surface((0, 0)),
                    rect=pygame.Rect(0, 0, 0, 0),
                    order=RenderableExtraOrder.Over,
                ),
                RenderableExtraKind.HealthBar: RenderableExtra(
                    image=pygame.Surface((0, 0)),
                    rect=pygame.Rect(0, 0, 0, 0),
                    order=RenderableExtraOrder.Over,
                ),
            },
        ),
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


def create_flame_turret(
    world: esper.World, build_zone_ent: int, *, assets: Assets
) -> int:
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
        ),
        bbox,
        Renderable(image=image, order=RenderableOrder.Objects),
    )


def create_frost_turret(
    world: esper.World, build_zone_ent: int, *, assets: Assets
) -> int:
    bz_bbox = world.component_for_entity(build_zone_ent, BoundingBox)

    image = assets.frost_turret
    image_rect = image.get_rect()

    bbox = BoundingBox(rect=Rect(image_rect))
    bbox.rect.center = bz_bbox.rect.center

    # for now, remove build zone entity, but may want to disable instead
    world.delete_entity(build_zone_ent)

    return world.create_entity(
        TurretMachine(
            state=TurretState.Idle,
            kind=TurretKind.Frost,
            firing_cooldown=2_000.0,
            firing_animation_duration=0,
        ),
        bbox,
        Renderable(image=image, order=RenderableOrder.Objects),
    )


def create_rocket_turret(
    world: esper.World, build_zone_ent: int, *, assets: Assets
) -> int:
    bz_bbox = world.component_for_entity(build_zone_ent, BoundingBox)

    image = assets.rocket_turret
    image_rect = image.get_rect()

    bbox = BoundingBox(rect=Rect(image_rect))
    bbox.rect.center = bz_bbox.rect.center

    # for now, remove build zone entity, but may want to disable instead
    world.delete_entity(build_zone_ent)

    return world.create_entity(
        TurretMachine(
            state=TurretState.Idle,
            kind=TurretKind.Rocket,
            firing_cooldown=2_000.0,
            firing_animation_duration=0,
            reloading_duration=500.0,
        ),
        bbox,
        Renderable(image=image, order=RenderableOrder.Objects),
    )


def create_bullet_turret(
    world: esper.World, build_zone_ent: int, *, assets: Assets
) -> int:
    bz_bbox = world.component_for_entity(build_zone_ent, BoundingBox)

    image = assets.bullet_turret
    image_rect = image.get_rect()

    bbox = BoundingBox(rect=Rect(image_rect))
    bbox.rect.center = bz_bbox.rect.center

    default_upgrade_levels = {
        TurretUpgradeablePropertyKind.Damage: 1,
        TurretUpgradeablePropertyKind.RateOfFire: 1,
        TurretUpgradeablePropertyKind.Range: 1,
    }

    # for now, remove build zone entity, but may want to disable instead
    world.delete_entity(build_zone_ent)

    return world.create_entity(
        TurretMachine(
            state=TurretState.Idle,
            kind=TurretKind.Bullet,
            upgrade_levels=default_upgrade_levels,
        ),
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

        case TurretKind.Frost:
            create_frost(world, turret_ent, enemy_ent, assets=assets)

        case TurretKind.Rocket:
            create_missile(world, turret_ent, enemy_ent, assets=assets)


def create_missile(
    world: esper.World, turret_ent: int, enemy_ent: int, *, assets: Assets
):
    turret_bbox = world.component_for_entity(turret_ent, BoundingBox)
    enemy_bbox = world.component_for_entity(enemy_ent, BoundingBox)

    image = assets.rocket_missile
    image_rect = image.get_rect()

    vec = (
        Vector2(enemy_bbox.rect.center) - Vector2(turret_bbox.rect.center)
    ).normalize()

    vec.scale_to_length(0.95)

    # missle should spawn inside turret, but centered
    missile_rect = Rect((0, 0), image_rect.size)
    missile_rect.center = turret_bbox.rect.center

    return world.create_entity(
        BoundingBox(rect=missile_rect, rotation=vec),
        Renderable(image=image, order=RenderableOrder.Objects),
        Velocity(vec=vec),
        RocketMissile(damage=15),
        RemoveOnOutOfBounds(),
        DamagesEnemy(
            damage=0,
            effects=[
                DamagesEnemyEffect(
                    kind=DamagesEnemyEffectKind.DynamicCreator,
                    dynamic_effect_creator=create_rocket_missile_explosion,
                )
            ],
        ),
    )


def create_rocket_missile_explosion(
    world: esper.World,
    source_ent: int,
    enemy_ent: int,
    *,
    assets: Assets,
):
    missile = world.component_for_entity(source_ent, RocketMissile)
    missile_bbox = world.component_for_entity(source_ent, BoundingBox)

    image = assets.rocket_missile_explosion
    image_rect = image.get_rect()

    # explosion should spawn at missile center
    explosion_rect = Rect((0, 0), image_rect.size)
    explosion_rect.center = missile_bbox.rect.center

    world.create_entity(
        BoundingBox(rect=explosion_rect),
        Renderable(image=image, order=RenderableOrder.Objects),
        TimeToLive(duration=250.0),
        DamagesEnemy(
            damage=missile.damage,
            pierced_count=9999,
            on_collision_behavior=DamagesEnemyOnCollisionBehavior.RemoveComponent,
        ),
    )


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
        BoundingBox(rect=flame_rect, rotation=vec),
        Renderable(image=image, order=RenderableOrder.Objects),
        Velocity(vec=vec),
        RemoveOnOutOfBounds(),
        TimeToLive(duration=500.0),
        DamagesEnemy(
            damage=0,
            effects=[
                DamagesEnemyEffect(
                    kind=DamagesEnemyEffectKind.AddsComponent,
                    component=Burning(
                        damage=1, damage_tick_rate=250.0, duration=1_000.0
                    ),
                )
            ],
        ),
    )


def create_frost(
    world: esper.World, turret_ent: int, enemy_ent: int, *, assets: Assets
):
    turret_bbox = world.component_for_entity(turret_ent, BoundingBox)
    enemy_bbox = world.component_for_entity(enemy_ent, BoundingBox)

    animated = Animated(frames=assets.frost_missile_frames, step=50.0)

    image = animated.current_frame
    image_rect = image.get_rect()

    vec = (
        Vector2(enemy_bbox.rect.center) - Vector2(turret_bbox.rect.center)
    ).normalize()

    # from 0.95
    vec.scale_to_length(0.5)

    # frost should spawn outside turret, not inside
    # let's adjust position along target vector
    turret_pos_offset = vec.copy()
    turret_pos_offset.scale_to_length(64)

    frost_center = Vector2(turret_bbox.rect.center) + turret_pos_offset

    frost_rect = Rect((0, 0), image_rect.size)
    frost_rect.center = (frost_center.x, frost_center.y)

    return world.create_entity(
        animated,
        BoundingBox(rect=frost_rect),
        Renderable(image=image, order=RenderableOrder.Objects),
        Velocity(vec=vec),
        RemoveOnOutOfBounds(),
        FrostMissile(damage=15),
        DamagesEnemy(
            damage=1,
            effects=[
                DamagesEnemyEffect(
                    kind=DamagesEnemyEffectKind.AddsComponent,
                    component=Frozen(duration=1_000.0),
                ),
                DamagesEnemyEffect(
                    kind=DamagesEnemyEffectKind.DynamicCreator,
                    dynamic_effect_creator=create_frost_missile_explosion,
                ),
            ],
        ),
    )


def create_frost_missile_explosion(
    world: esper.World,
    source_ent: int,
    enemy_ent: int,
    *,
    assets: Assets,
):
    frost = world.component_for_entity(source_ent, FrostMissile)
    frost_bbox = world.component_for_entity(source_ent, BoundingBox)

    animated = Animated(frames=assets.frost_missile_explosion_frames, step=50.0)
    base_image = animated.current_frame
    image_rect = base_image.get_rect()

    # explosion should spawn at frost center
    explosion_rect = Rect((0, 0), image_rect.size)
    explosion_rect.center = frost_bbox.rect.center

    world.create_entity(
        animated,
        BoundingBox(rect=explosion_rect),
        Renderable(image=base_image, order=RenderableOrder.Objects),
        TimeToLive(duration=800.0),  # synced with animation
        DamagesEnemy(
            damage=frost.damage,
            pierced_count=9999,
            on_collision_behavior=DamagesEnemyOnCollisionBehavior.RemoveComponent,
        ),
    )


def apply_damage_effects_to_enemy(
    world: esper.World, source_ent: int, enemy_ent: int, *, assets: Assets
):
    damages_enemy = world.component_for_entity(source_ent, DamagesEnemy)

    for effect in damages_enemy.effects:
        match effect:
            case DamagesEnemyEffect(
                kind=DamagesEnemyEffectKind.AddsComponent, component=component
            ):
                world.add_component(enemy_ent, component)
            case DamagesEnemyEffect(
                kind=DamagesEnemyEffectKind.DynamicCreator,
                dynamic_effect_creator=dynamic_effect_creator,
            ):
                dynamic_effect_creator(world, source_ent, enemy_ent, assets=assets)


def create_bullet(world: esper.World, turret_ent: int, enemy_ent: int) -> int:
    turret_machine = world.component_for_entity(turret_ent, TurretMachine)

    enemy_bbox = world.component_for_entity(enemy_ent, BoundingBox)

    bullet_size = 12, 12

    return world.create_entity(
        # spawn bullet on top of enemy, "instantaneous" damage
        BoundingBox(rect=Rect(enemy_bbox.rect.center, bullet_size)),
        DamagesEnemy(damage=turret_machine.damage),
        # possible that bullet spawns and doesnt hit enemy due to enemy dying
        # to other damage, so let's not let the bullet linger
        TimeToLive(50.0),
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


def upgrade_turret(
    world: esper.World, turret_ent: int, turret_property: TurretUpgradeablePropertyKind
):
    turret = world.component_for_entity(turret_ent, TurretMachine)

    turret.upgrade_levels[turret_property] += 1
