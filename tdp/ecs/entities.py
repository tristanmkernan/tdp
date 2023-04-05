import logging
import random

import pygame

from pygame import Rect, Vector2


from ..constants import MAX_TURRET_PROPERTY_UPGRADE_LEVEL, PLAYER_STARTING_MONEY

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
    TurretBuildZone,
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
from .resources import add_resources_from_turret_sale

from . import esper

logger = logging.getLogger(__name__)


def create_scoreboard(world: esper.World):
    scoreboard = world.create_entity()

    world.add_component(scoreboard, ScoreTracker())


def spawn_tank(world: esper.World, spawn_point: int, level: int, *, assets: Assets):
    base_health = 100
    per_level = 5

    max_health = base_health + level * per_level

    base_bounty = 25
    bounty_per_level = 5

    bounty = base_bounty + level * bounty_per_level

    return spawn_enemy(
        world, spawn_point, assets.tank, bounty=bounty, max_health=max_health
    )


def spawn_grunt(world: esper.World, spawn_point: int, level: int, *, assets: Assets):
    base_health = 30
    per_level = 8

    max_health = base_health + level * per_level

    base_bounty = 3
    bounty_per_level = 0

    bounty = base_bounty + level * bounty_per_level

    return spawn_enemy(
        world, spawn_point, assets.grunt, bounty=bounty, max_health=max_health
    )


def spawn_elite(world: esper.World, spawn_point: int, level: int, *, assets: Assets):
    base_health = 50
    per_level = 25

    max_health = base_health + level * per_level

    base_bounty = 10
    bounty_per_level = 0

    bounty = base_bounty + level * bounty_per_level

    return spawn_enemy(
        world, spawn_point, assets.elite, bounty=bounty, max_health=max_health
    )


def spawn_commando(world: esper.World, spawn_point: int, level: int, *, assets: Assets):
    base_health = 80
    per_level = 40

    max_health = base_health + level * per_level

    base_bounty = 15
    bounty_per_level = 0

    bounty = base_bounty + level * bounty_per_level

    return spawn_enemy(
        world, spawn_point, assets.commando, bounty=bounty, max_health=max_health
    )


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

    # increase score
    track_score_event(world, ScoreEventKind.EnemyKill)


def create_flame_turret(
    world: esper.World, build_zone_ent: int, *, assets: Assets
) -> int:
    bz_bbox = world.component_for_entity(build_zone_ent, BoundingBox)

    image = assets.flame_turret
    image_rect = image.get_rect()

    bbox = BoundingBox(rect=Rect(image_rect))
    bbox.rect.center = bz_bbox.rect.center

    upgrade_levels = {
        TurretUpgradeablePropertyKind.Damage: 1,
        TurretUpgradeablePropertyKind.RateOfFire: 1,
        TurretUpgradeablePropertyKind.Range: 1,
    }

    base_stats = {
        TurretUpgradeablePropertyKind.Damage: 3,
        TurretUpgradeablePropertyKind.RateOfFire: 25.0,
        TurretUpgradeablePropertyKind.Range: 200.0,
    }

    stat_changes_per_level = {
        TurretUpgradeablePropertyKind.Damage: 3,
        TurretUpgradeablePropertyKind.RateOfFire: -5.0,
        TurretUpgradeablePropertyKind.Range: 25.0,
    }

    # for now, remove build zone entity, but may want to disable instead
    world.delete_entity(build_zone_ent)

    return world.create_entity(
        TurretMachine(
            state=TurretState.Idle,
            kind=TurretKind.Flame,
            firing_animation_duration=0,
            upgrade_levels=upgrade_levels,
            base_stats=base_stats,
            stat_changes_per_level=stat_changes_per_level,
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

    upgrade_levels = {
        TurretUpgradeablePropertyKind.Damage: 1,
        TurretUpgradeablePropertyKind.RateOfFire: 1,
        TurretUpgradeablePropertyKind.Range: 1,
    }

    base_stats = {
        TurretUpgradeablePropertyKind.Damage: 3,
        TurretUpgradeablePropertyKind.RateOfFire: 2000.0,
        TurretUpgradeablePropertyKind.Range: 500.0,
    }

    stat_changes_per_level = {
        TurretUpgradeablePropertyKind.Damage: 2,
        TurretUpgradeablePropertyKind.RateOfFire: -150.0,
        TurretUpgradeablePropertyKind.Range: 100.0,
    }

    # for now, remove build zone entity, but may want to disable instead
    world.delete_entity(build_zone_ent)

    return world.create_entity(
        TurretMachine(
            state=TurretState.Idle,
            kind=TurretKind.Frost,
            firing_animation_duration=0,
            upgrade_levels=upgrade_levels,
            base_stats=base_stats,
            stat_changes_per_level=stat_changes_per_level,
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

    upgrade_levels = {
        TurretUpgradeablePropertyKind.Damage: 1,
        TurretUpgradeablePropertyKind.RateOfFire: 1,
        TurretUpgradeablePropertyKind.Range: 1,
    }

    base_stats = {
        TurretUpgradeablePropertyKind.Damage: 15,
        TurretUpgradeablePropertyKind.RateOfFire: 2000.0,
        TurretUpgradeablePropertyKind.Range: 500.0,
    }

    stat_changes_per_level = {
        TurretUpgradeablePropertyKind.Damage: 10,
        TurretUpgradeablePropertyKind.RateOfFire: -150.0,
        TurretUpgradeablePropertyKind.Range: 100.0,
    }

    # for now, remove build zone entity, but may want to disable instead
    world.delete_entity(build_zone_ent)

    return world.create_entity(
        TurretMachine(
            state=TurretState.Idle,
            kind=TurretKind.Rocket,
            firing_animation_duration=0,
            reloading_duration=500.0,
            upgrade_levels=upgrade_levels,
            base_stats=base_stats,
            stat_changes_per_level=stat_changes_per_level,
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

    upgrade_levels = {
        TurretUpgradeablePropertyKind.Damage: 1,
        TurretUpgradeablePropertyKind.RateOfFire: 1,
        TurretUpgradeablePropertyKind.Range: 1,
    }

    base_stats = {
        TurretUpgradeablePropertyKind.Damage: 10,
        TurretUpgradeablePropertyKind.RateOfFire: 1000.0,
        TurretUpgradeablePropertyKind.Range: 200.0,
    }

    stat_changes_per_level = {
        TurretUpgradeablePropertyKind.Damage: 5,
        TurretUpgradeablePropertyKind.RateOfFire: -75.0,
        TurretUpgradeablePropertyKind.Range: 50.0,
    }

    # for now, remove build zone entity, but may want to disable instead
    world.delete_entity(build_zone_ent)

    return world.create_entity(
        TurretMachine(
            state=TurretState.Idle,
            kind=TurretKind.Bullet,
            upgrade_levels=upgrade_levels,
            base_stats=base_stats,
            stat_changes_per_level=stat_changes_per_level,
            # sync'd with max rate of fire
            firing_animation_duration=250.0,
        ),
        bbox,
        Renderable(image=image, order=RenderableOrder.Objects),
    )


def create_lightning_turret(
    world: esper.World, build_zone_ent: int, *, assets: Assets
) -> int:
    bz_bbox = world.component_for_entity(build_zone_ent, BoundingBox)

    image = assets.lightning_turret
    image_rect = image.get_rect()

    bbox = BoundingBox(rect=Rect(image_rect))
    bbox.rect.center = bz_bbox.rect.center

    upgrade_levels = {
        TurretUpgradeablePropertyKind.Damage: 1,
        TurretUpgradeablePropertyKind.RateOfFire: 1,
        TurretUpgradeablePropertyKind.Range: 1,
    }

    base_stats = {
        TurretUpgradeablePropertyKind.Damage: 25,
        TurretUpgradeablePropertyKind.RateOfFire: 5_000.0,
        TurretUpgradeablePropertyKind.Range: 300.0,
    }

    stat_changes_per_level = {
        TurretUpgradeablePropertyKind.Damage: 5,
        TurretUpgradeablePropertyKind.RateOfFire: -200.0,
        TurretUpgradeablePropertyKind.Range: 50.0,
    }

    # for now, remove build zone entity, but may want to disable instead
    world.delete_entity(build_zone_ent)

    return world.create_entity(
        TurretMachine(
            state=TurretState.Idle,
            kind=TurretKind.Lightning,
            upgrade_levels=upgrade_levels,
            base_stats=base_stats,
            stat_changes_per_level=stat_changes_per_level,
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

        case TurretKind.Lightning:
            create_lightning_strike(world, turret_ent, enemy_ent, assets=assets)


def create_missile(
    world: esper.World, turret_ent: int, enemy_ent: int, *, assets: Assets
):
    turret_bbox = world.component_for_entity(turret_ent, BoundingBox)
    turret_machine = world.component_for_entity(turret_ent, TurretMachine)
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
        RocketMissile(damage=turret_machine.damage),
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


def create_lightning_strike(
    world: esper.World,
    turret_ent: int,
    enemy_ent: int,
    *,
    assets: Assets,
):
    turret_machine = world.component_for_entity(turret_ent, TurretMachine)
    enemy_bbox = world.component_for_entity(enemy_ent, BoundingBox)

    animated = Animated(frames=assets.lightning_strike_frames, step=50.0)
    base_image = animated.current_frame
    image_rect = base_image.get_rect()

    # explosion should spawn at missile center
    explosion_rect = Rect((0, 0), image_rect.size)
    explosion_rect.center = enemy_bbox.rect.center

    world.create_entity(
        animated,
        BoundingBox(rect=explosion_rect),
        Renderable(image=base_image, order=RenderableOrder.Objects),
        TimeToLive(duration=800.0),  # sync'd with animation
        DamagesEnemy(
            damage=turret_machine.damage,
            pierced_count=9999,
            on_collision_behavior=DamagesEnemyOnCollisionBehavior.RemoveComponent,
            effects=[
                DamagesEnemyEffect(
                    kind=DamagesEnemyEffectKind.DynamicCreator,
                    dynamic_effect_creator=create_lightning_strike_chain_lightning,
                ),
            ],
        ),
    )


def create_lightning_strike_chain_lightning(
    world: esper.World,
    source_ent: int,
    enemy_ent: int,
    *,
    assets: Assets,
):
    # TODO
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


def create_flame(
    world: esper.World, turret_ent: int, enemy_ent: int, *, assets: Assets
):
    turret_bbox = world.component_for_entity(turret_ent, BoundingBox)
    turret_machine = world.component_for_entity(turret_ent, TurretMachine)
    enemy_bbox = world.component_for_entity(enemy_ent, BoundingBox)

    image = assets.flame_particle
    image_rect = image.get_rect()

    vec = (
        Vector2(enemy_bbox.rect.center) - Vector2(turret_bbox.rect.center)
    ).normalize()

    # introduce random rotation, flame turret creates "cone" of flame
    # +30, -30 deg range (60 deg total cone)
    vec = vec.rotate(random.uniform(-30.0, 30.0))

    speed = 0.20
    vec.scale_to_length(speed)

    duration = turret_machine.range / speed

    # flame should spawn outside turret, not inside
    # let's adjust position along target vector
    turret_pos_offset = vec.copy()
    turret_pos_offset.scale_to_length(40)

    flame_center = Vector2(turret_bbox.rect.center) + turret_pos_offset

    flame_rect = Rect((0, 0), image_rect.size)
    flame_rect.center = (flame_center.x, flame_center.y)

    return world.create_entity(
        BoundingBox(rect=flame_rect, rotation=vec),
        Renderable(image=image, order=RenderableOrder.Objects),
        Velocity(vec=vec),
        RemoveOnOutOfBounds(),
        TimeToLive(duration=duration),
        DamagesEnemy(
            damage=0,
            pierces=9999,
            effects=[
                DamagesEnemyEffect(
                    kind=DamagesEnemyEffectKind.AddsComponent,
                    overwrite=False,
                    component=Burning(
                        # TODO consider scaling damage on tick rate or duration
                        # or adding more upgradeable properties custom per turret
                        damage=turret_machine.damage,
                        damage_tick_rate=500.0,
                        duration=3_000.0,
                    ),
                )
            ],
        ),
    )


def create_frost(
    world: esper.World, turret_ent: int, enemy_ent: int, *, assets: Assets
):
    turret_bbox = world.component_for_entity(turret_ent, BoundingBox)
    turret_machine = world.component_for_entity(turret_ent, TurretMachine)
    enemy_bbox = world.component_for_entity(enemy_ent, BoundingBox)

    animated = Animated(frames=assets.frost_missile_frames, step=50.0)

    image = animated.current_frame
    image_rect = image.get_rect()

    vec = (
        Vector2(enemy_bbox.rect.center) - Vector2(turret_bbox.rect.center)
    ).normalize()

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
        FrostMissile(damage=turret_machine.damage),
        DamagesEnemy(
            damage=1,
            effects=[
                DamagesEnemyEffect(
                    kind=DamagesEnemyEffectKind.AddsComponent,
                    overwrite=False,
                    # TODO could scale with damage or custom property
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
                kind=DamagesEnemyEffectKind.AddsComponent,
                component=component,
                overwrite=overwrite,
            ):
                # TODO reconsider using type()
                if not overwrite and (
                    existing_component := world.try_component(
                        enemy_ent, type(component)
                    )
                ):
                    existing_component.reapply(component)
                else:
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

    score_tracker.scores[kind] += 1


def turret_property_can_be_upgraded(
    world: esper.World, turret_ent: int, turret_property: TurretUpgradeablePropertyKind
) -> bool:
    turret = world.component_for_entity(turret_ent, TurretMachine)

    return turret.upgrade_levels[turret_property] < MAX_TURRET_PROPERTY_UPGRADE_LEVEL


def upgrade_turret(
    world: esper.World, turret_ent: int, turret_property: TurretUpgradeablePropertyKind
):
    turret = world.component_for_entity(turret_ent, TurretMachine)

    turret.upgrade_levels[turret_property] = min(
        MAX_TURRET_PROPERTY_UPGRADE_LEVEL, turret.upgrade_levels[turret_property] + 1
    )


def sync_selected_turret_range_extra_renderable(
    world: esper.World,
    turret_ent: int | None,
) -> None:
    # hide all other range extra renderables
    for _, (_, other_renderable) in world.get_components(TurretMachine, Renderable):
        other_renderable.extras.pop(RenderableExtraKind.TurretRange, None)

    # add selected turret range
    if turret_ent is None:
        return

    turret_machine = world.component_for_entity(turret_ent, TurretMachine)
    renderable = world.component_for_entity(turret_ent, Renderable)
    bbox = world.component_for_entity(turret_ent, BoundingBox)

    range_extra_renderable = renderable.extras[RenderableExtraKind.TurretRange]

    range = turret_machine.range
    range_image_dim = range * 2 + 20

    range_image = pygame.Surface((range_image_dim, range_image_dim), pygame.SRCALPHA)

    pygame.draw.circle(
        range_image,
        "#ff3300",
        (range_image_dim / 2, range_image_dim / 2),
        range,
        width=2,
    )

    # positioned centered on turret
    range_rect = range_image.get_rect()
    range_rect.center = bbox.rect.center

    range_extra_renderable.image = range_image
    range_extra_renderable.order = RenderableExtraOrder.Over
    range_extra_renderable.rect = range_rect


def sell_turret(world: esper.World, turret_ent: int, *, assets: Assets):
    # create turret build zone in its place
    bbox = world.component_for_entity(turret_ent, BoundingBox)

    image = assets.turret_build_zone
    image_rect = image.get_rect()

    image_rect.center = bbox.rect.center

    world.create_entity(
        Renderable(
            image=image,
            order=RenderableOrder.Objects,
        ),
        BoundingBox(rect=image_rect),
        TurretBuildZone(),
    )

    # increase money
    add_resources_from_turret_sale(world, turret_ent)

    # delete turret
    world.delete_entity(turret_ent)
