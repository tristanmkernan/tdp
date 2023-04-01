import logging

import pygame
import pygame.constants
from pygame import Vector2, Rect

from tdp.constants import MAP_HEIGHT, MAP_WIDTH

from .assets import Assets
from .gui import GuiElements, sync_selected_turret_gui
from .types import PlayerAction
from .components import (
    Animated,
    BoundingBox,
    Burning,
    DamagesEnemy,
    Enemy,
    Lifetime,
    PlayerInputMachine,
    PlayerResources,
    RemoveOnOutOfBounds,
    TimeToLive,
    TurretMachine,
    Velocity,
    Spawning,
    Renderable,
    ScoreTracker,
    UnitPathing,
    Despawnable,
    Despawning,
    VelocityAdjustment,
)
from .entities import (
    apply_damage_effects_to_enemy,
    create_frost_turret,
    fire_turret,
    create_flame_turret,
    create_bullet_turret,
    create_rocket_turret,
    kill_enemy,
    spawn_grunt,
    spawn_tank,
    sync_selected_turret_range_extra_renderable,
    track_score_event,
    turret_property_can_be_upgraded,
    upgrade_turret,
)
from .enums import (
    DamagesEnemyOnCollisionBehavior,
    EnemyKind,
    PlayerInputState,
    RenderableExtraKind,
    RenderableExtraOrder,
    ScoreEventKind,
    InputEventKind,
    PlayerActionKind,
    SpawningWaveStepKind,
    TurretKind,
    TurretState,
    VelocityAdjustmentKind,
)
from .rendering import render_composite, render_simple
from .resources import (
    player_has_resources_to_build_turret,
    player_has_resources_to_upgrade_turret,
    subtract_resources_to_build_turret,
    subtract_resources_to_upgrade_turret,
)
from .util import (
    get_player_action_for_button_press,
    get_player_action_for_click,
    get_closest_enemy,
)
from . import esper

logger = logging.getLogger(__name__)


def add_systems(world: esper.World):
    world.add_processor(PlayerResourcesProcessor())
    world.add_processor(TurretStateProcessor())
    world.add_processor(BurningProcessor())
    world.add_processor(EnemyStatusVisualEffectProcessor())
    world.add_processor(TimeToLiveProcessor())
    world.add_processor(MovementProcessor())

    world.add_processor(SpawningProcessor())
    world.add_processor(OutOfBoundsProcessor())
    world.add_processor(DamagesEnemyProcessor())
    world.add_processor(PlayerInputProcessor())
    #    world.add_processor(ScoreTimeTrackerProcessor())
    world.add_processor(LifetimeProcessor())
    world.add_processor(PathingProcessor())
    world.add_processor(DespawningProcessor())

    world.add_processor(AnimationProcessor())
    world.add_processor(RotationProcessor())
    world.add_processor(RenderingProcessor())


class MovementProcessor(esper.Processor):
    def process(self, *args, delta: float, **kwargs):
        for _, (vel, bbox) in self.world.get_components(Velocity, BoundingBox):
            velocity_vector = vel.vec.copy()

            # dynamic adjustments from e.g. status effects
            for adjustment in vel.adjustments.values():
                match adjustment:
                    case VelocityAdjustment(kind=VelocityAdjustmentKind.Immobile):
                        velocity_vector.scale_to_length(0.0)
                    case VelocityAdjustment(
                        kind=VelocityAdjustmentKind.Slowdown, magnitude=magnitude
                    ):
                        velocity_vector.scale_to_length(magnitude)

            # update position
            bbox.rect.centerx += velocity_vector.x * delta
            bbox.rect.centery += velocity_vector.y * delta

            # update adjustments
            to_remove = []

            for adjustment_kind, adjustment in vel.adjustments.items():
                adjustment.elapsed += delta

                if adjustment.expired:
                    to_remove.append(adjustment_kind)

            for key in to_remove:
                del vel.adjustments[key]


class SpawningProcessor(esper.Processor):
    def process(self, *args, delta, gui_elements: GuiElements, assets, **kwargs):
        # NOTE: only one spawn point at the moment
        spawning_ent, spawning = self.world.get_component(Spawning)[0]

        wave = spawning.current_wave

        current_step = wave.current_step

        match current_step:
            case {"kind": SpawningWaveStepKind.SpawnEnemy, "enemy_kind": enemy_kind}:
                match enemy_kind:
                    case EnemyKind.Grunt:
                        enemy = spawn_grunt(self.world, spawning_ent, assets=assets)
                    case EnemyKind.Tank:
                        enemy = spawn_tank(self.world, spawning_ent, assets=assets)

                wave.enemy_spawn_count += 1
                wave.advance()

                logger.info("Spawned new enemy id=%d", enemy)

            case {"kind": SpawningWaveStepKind.Wait, "duration": duration}:
                wave.elapsed += delta

                if wave.elapsed >= duration:
                    wave.advance()

        if wave.over:
            spawning.advance()

        # update ui
        gui_elements.wave_label.set_text(f"Wave {spawning.current_wave_num}")

        gui_elements.wave_progress.set_current_progress(wave.progress)


class RenderingProcessor(esper.Processor):
    def __init__(self) -> None:
        super().__init__()

        self.font = pygame.font.SysFont("Comic", 40)

    def process(self, *args, show_fps, screen, clock, debug, gui_manager, **kwargs):
        screen.fill((255, 255, 255))

        renderables = self.world.get_components(Renderable, BoundingBox)

        # sort by z-index to display in correct order
        renderables = sorted(renderables, key=lambda item: item[1][0].order)

        for _, (renderable, bbox) in renderables:
            if renderable.composite:
                render_composite(screen, renderable, bbox)
            else:
                render_simple(screen, renderable, bbox)

            # render bounding box in debug mode
            if debug:
                pygame.draw.rect(screen, (0, 0, 0), bbox.rect, 2)

        if show_fps:
            fps_str = f"{clock.get_fps():.1f}"

            fps_overlay = self.font.render(fps_str, True, pygame.Color(0, 0, 0))

            screen.blit(fps_overlay, (0, 0))

        gui_manager.draw_ui(screen)

        pygame.display.flip()


class OutOfBoundsProcessor(esper.Processor):
    def process(self, *args, **kwargs):
        screen_rect = Rect((0, 0), (MAP_WIDTH, MAP_HEIGHT))

        for ent, (_, bbox) in self.world.get_components(
            RemoveOnOutOfBounds, BoundingBox
        ):
            if not bbox.rect.colliderect(screen_rect):
                logger.info("Entity out of bounds id=%d", ent)
                self.world.delete_entity(ent)


# TODO refactor to EnemyCollisionProcessor
# applying Damage is just another CollisionEffect
class DamagesEnemyProcessor(esper.Processor):
    def process(self, *args, assets: Assets, **kwargs):
        for damaging_ent, (damages_enemy, damaging_bbox) in self.world.get_components(
            DamagesEnemy, BoundingBox
        ):
            for enemy_ent, (
                enemy,
                enemy_bbox,
            ) in self.world.get_components(Enemy, BoundingBox):
                if damaging_bbox.rect.colliderect(enemy_bbox.rect):
                    logger.debug("Damaging entity id=%d", enemy_ent)

                    enemy.take_damage(damages_enemy.damage)

                    if enemy.is_dead:
                        track_score_event(self.world, ScoreEventKind.EnemyKill)

                        kill_enemy(self.world, enemy_ent)
                    elif damages_enemy.applies_effects:
                        apply_damage_effects_to_enemy(
                            self.world, damaging_ent, enemy_ent, assets=assets
                        )

                    damages_enemy.pierced_count += 1

                    if damages_enemy.expired:
                        match damages_enemy.on_collision_behavior:
                            case DamagesEnemyOnCollisionBehavior.DeleteEntity:
                                self.world.delete_entity(damaging_ent)
                            case DamagesEnemyOnCollisionBehavior.RemoveComponent:
                                self.world.remove_component(damaging_ent, DamagesEnemy)

                        break


class PlayerInputProcessor(esper.Processor):
    def process(self, *args, assets: Assets, gui_elements: GuiElements, **kwargs):
        # TODO consider sorting by keydown, then keyup,
        #   in case we receive a sequence "out of order" like
        #   [W key up, W key down]
        input_events = kwargs["player_input_events"]
        player_actions: list[PlayerAction] = []

        player_input_machine = self.world.get_component(PlayerInputMachine)[0][1]

        for input_event in input_events:
            logger.debug(
                "Processing player input event kind=%d all=%s",
                input_event["kind"],
                input_event,
            )

            match input_event:
                case {"kind": InputEventKind.MouseLeftClickUp, "pos": pos}:
                    # may or may not click on an object
                    if action := get_player_action_for_click(self.world, pos):
                        player_actions.append(action)
                case {"kind": InputEventKind.UIButtonPress, "ui_element": ui_element}:
                    if action := get_player_action_for_button_press(
                        self.world, ui_element, gui_elements
                    ):
                        player_actions.append(action)

        acceptable_actions: dict[PlayerInputState, set[PlayerActionKind]] = {
            PlayerInputState.Idle: {
                PlayerActionKind.SetTurretToBuild,
                PlayerActionKind.SelectTurret,
            },
            PlayerInputState.SelectingTurret: {
                PlayerActionKind.SelectTurret,
                PlayerActionKind.UpgradeTurretProperty,
                PlayerActionKind.SetTurretToBuild,
            },
            PlayerInputState.BuildingTurret: {
                PlayerActionKind.ClearTurretToBuild,
                PlayerActionKind.SetTurretToBuild,
                PlayerActionKind.SelectTurretBuildZone,
            },
        }

        changed_selected_turret = False
        changed_turret_to_build = False

        for action in player_actions:
            if not action["kind"] in acceptable_actions[player_input_machine.state]:
                continue

            match action:
                case {"kind": PlayerActionKind.SelectTurret, "ent": ent}:
                    player_input_machine.state = PlayerInputState.SelectingTurret
                    player_input_machine.selected_turret = ent

                    changed_selected_turret = True

                case {
                    "kind": PlayerActionKind.UpgradeTurretProperty,
                    "turret_property": turret_property,
                }:
                    if player_has_resources_to_upgrade_turret(
                        self.world, turret_property
                    ) and turret_property_can_be_upgraded(
                        self.world,
                        player_input_machine.selected_turret,
                        turret_property,
                    ):
                        upgrade_turret(
                            self.world,
                            player_input_machine.selected_turret,
                            turret_property,
                        )

                        subtract_resources_to_upgrade_turret(
                            self.world, turret_property
                        )

                        changed_selected_turret = True

                case {
                    "kind": PlayerActionKind.SetTurretToBuild,
                    "turret_kind": turret_kind,
                }:
                    if player_has_resources_to_build_turret(self.world, turret_kind):
                        player_input_machine.turret_to_build = turret_kind
                        player_input_machine.state = PlayerInputState.BuildingTurret

                        changed_turret_to_build = True

                case {"kind": PlayerActionKind.ClearTurretToBuild}:
                    player_input_machine.turret_to_build = None
                    player_input_machine.state = PlayerInputState.Idle

                    changed_turret_to_build = True

                case {"kind": PlayerActionKind.SelectTurretBuildZone, "ent": ent}:
                    # for now, let's just build a turret here
                    # TODO also could have hover state, building time, so on
                    new_turret_ent = None

                    match player_input_machine.turret_to_build:
                        case TurretKind.Flame:
                            new_turret_ent = create_flame_turret(
                                self.world, ent, assets=assets
                            )
                        case TurretKind.Bullet:
                            new_turret_ent = create_bullet_turret(
                                self.world, ent, assets=assets
                            )
                        case TurretKind.Rocket:
                            new_turret_ent = create_rocket_turret(
                                self.world, ent, assets=assets
                            )
                        case TurretKind.Frost:
                            new_turret_ent = create_frost_turret(
                                self.world, ent, assets=assets
                            )

                    subtract_resources_to_build_turret(
                        self.world, player_input_machine.turret_to_build
                    )

                    player_input_machine.state = PlayerInputState.SelectingTurret
                    player_input_machine.turret_to_build = None
                    player_input_machine.selected_turret = new_turret_ent

                    changed_turret_to_build = True
                    changed_selected_turret = True

        if changed_turret_to_build:
            # maybe add a border (or other visual effect) to the selected turret button
            turret_gui_element_map = {
                TurretKind.Bullet: gui_elements.basic_turret_build_button,
                TurretKind.Flame: gui_elements.flame_turret_build_button,
                TurretKind.Frost: gui_elements.frost_turret_build_button,
                TurretKind.Rocket: gui_elements.rocket_turret_build_button,
            }

            match player_input_machine.state:
                case PlayerInputState.BuildingTurret:
                    # reset button classes
                    for gui_button in turret_gui_element_map.values():
                        gui_button.enable()

                    if gui_button := turret_gui_element_map.get(
                        player_input_machine.turret_to_build
                    ):
                        gui_button.disable()
                case _:
                    # reset button classes
                    for gui_button in turret_gui_element_map.values():
                        gui_button.enable()

        if changed_selected_turret:
            if player_input_machine.selected_turret:
                # update selected turret ui
                sync_selected_turret_gui(
                    self.world, player_input_machine.selected_turret, gui_elements
                )

                # sync range ring extra renderable for turret
                sync_selected_turret_range_extra_renderable(
                    self.world,
                    player_input_machine.selected_turret,
                )

                gui_elements.selected_turret_panel.show()
            else:
                # if no selected turret, hide the selected turret ui
                gui_elements.selected_turret_panel.hide()


class ScoreTimeTrackerProcessor(esper.Processor):
    def process(self, *args, delta, **kwargs):
        for _, score_tracker in self.world.get_component(ScoreTracker):
            score_tracker.scores[ScoreEventKind.Time] += delta / 1_000.0


class LifetimeProcessor(esper.Processor):
    def process(self, *args, delta, **kwargs):
        for ent, lifetime in self.world.get_component(Lifetime):
            lifetime.remaining -= delta

            if lifetime.remaining < 0.0:
                self.world.delete_entity(ent)


class PathingProcessor(esper.Processor):
    def process(self, *args, **kwargs):
        for ent, (pathing, bbox, vel) in self.world.get_components(
            UnitPathing, BoundingBox, Velocity
        ):
            # check if unit has reached the target
            target_vertex = pathing.current_target

            if bbox.rect.collidepoint(target_vertex):
                pathing.advance()

            # update velocity
            target_vertex = pathing.current_target

            # TODO speed should be determined by base velocity
            vec = (target_vertex - Vector2(*bbox.rect.center)).normalize()
            vec.scale_to_length(0.1)

            vel.vec = vec

            # orient towards the next vertex
            bbox.rotation = vec


class DespawningProcessor(esper.Processor):
    def process(self, *args, delta, **kwargs):
        # TODO clean this up
        # could be more efficient than N^2
        for _, (despawning, despawn_bbox) in self.world.get_components(
            Despawning, BoundingBox
        ):
            for ent, (despawnable, ent_bbox) in self.world.get_components(
                Despawnable, BoundingBox
            ):
                if despawn_bbox.rect.colliderect(ent_bbox.rect):
                    logger.info("Despawning entity id=%d", ent)

                    track_score_event(self.world, ScoreEventKind.EnemyDespawn)

                    self.world.delete_entity(ent)


class RotationProcessor(esper.Processor):
    # TODO need to combine with rendering somehow
    def process(self, *args, **kwargs):
        for _, (renderable, bbox) in self.world.get_components(Renderable, BoundingBox):
            # sync the bbox and rotation

            renderable.image = pygame.transform.rotate(
                renderable.original_image, bbox.rotation.angle_to(Vector2())
            )

            updated_rect = renderable.image.get_rect()

            # around what point is rotation performed?
            updated_rect.center = bbox.rect.center

            bbox.rect = updated_rect


class AnimationProcessor(esper.Processor):
    # TODO need to combine with rendering somehow
    # TODO incompatible with rotation right now, unless synced in order?
    def process(self, *args, delta: float, **kwargs):
        for _, (animated, renderable) in self.world.get_components(
            Animated, Renderable
        ):
            animated.elapsed += delta

            if animated.frame_expired:
                animated.advance_frame()

                # not expected that animation changes bbox
                renderable.original_image = renderable.image = animated.current_frame


class TurretStateProcessor(esper.Processor):
    def process(self, *args, delta, assets: Assets, **kwargs):
        for turret_ent, (
            turret_machine,
            turret_bbox,
            renderable,
        ) in self.world.get_components(TurretMachine, BoundingBox, Renderable):
            turret_machine.elapsed += delta

            closest_enemy = get_closest_enemy(
                self.world, turret_bbox, range=turret_machine.range
            )

            match turret_machine.state:
                case TurretState.Idle:
                    # if enemy, transition to tracking
                    if closest_enemy:
                        turret_machine.state = TurretState.Tracking
                    else:
                        # slowly rotate
                        turret_bbox.rotation = turret_bbox.rotation.rotate(
                            turret_machine.idle_rotation_speed * delta
                        )

                case TurretState.FiringAnimation:
                    if turret_machine.finished_firing_animation:
                        turret_machine.state = TurretState.Reloading

                case TurretState.Reloading:
                    if turret_machine.finished_reloading:
                        turret_machine.state = TurretState.Tracking

                case TurretState.Firing:
                    # if no enemy, transition to idle
                    if not closest_enemy:
                        turret_machine.state = TurretState.Idle
                    else:
                        # rotate towards enemy
                        enemy_bbox = self.world.component_for_entity(
                            closest_enemy, BoundingBox
                        )

                        turret_bbox.rotation = Vector2(
                            enemy_bbox.rect.center
                        ) - Vector2(turret_bbox.rect.center)

                        fire_turret(
                            self.world,
                            turret_ent,
                            turret_machine,
                            closest_enemy,
                            assets=assets,
                        )

                        turret_machine.elapsed = 0.0

                        # transition to animating
                        turret_machine.state = TurretState.FiringAnimation

                case TurretState.Tracking:
                    # if no enemy, transition to idle
                    if not closest_enemy:
                        turret_machine.state = TurretState.Idle
                    else:
                        # rotate towards enemy
                        enemy_bbox = self.world.component_for_entity(
                            closest_enemy, BoundingBox
                        )

                        turret_bbox.rotation = Vector2(
                            enemy_bbox.rect.center
                        ) - Vector2(turret_bbox.rect.center)

                        # if possible, transition to firing
                        if turret_machine.can_fire:
                            turret_machine.state = TurretState.Firing

            # sync state and sprite
            match (turret_machine.kind, turret_machine.state):
                case (TurretKind.Bullet, TurretState.FiringAnimation):
                    renderable.image = (
                        renderable.original_image
                    ) = assets.bullet_turret__firing
                case (TurretKind.Rocket, TurretState.Reloading):
                    renderable.image = (
                        renderable.original_image
                    ) = assets.rocket_turret__reloading
                case (TurretKind.Bullet, _):
                    renderable.image = renderable.original_image = assets.bullet_turret
                case (TurretKind.Flame, _):
                    renderable.image = renderable.original_image = assets.flame_turret
                case (TurretKind.Rocket, _):
                    renderable.image = renderable.original_image = assets.rocket_turret


class PlayerResourcesProcessor(esper.Processor):
    def process(self, *args, gui_elements: GuiElements, **kwargs):
        # update the resources label with the current player resources
        player_resources = self.world.get_component(PlayerResources)[0][1]

        gui_elements.resources_label.set_text(f"Money: ${player_resources.money}")


class TimeToLiveProcessor(esper.Processor):
    def process(self, *args, delta: float, **kwargs):
        for ent, time_to_live in self.world.get_component(TimeToLive):
            time_to_live.elapsed += delta

            if time_to_live.expired:
                self.world.delete_entity(ent)


# TODO TransformationProcessor
class FadeOutProcessor(esper.Processor):
    def process(self, *args, delta: float, **kwargs):
        pass


class BurningProcessor(esper.Processor):
    def process(self, *args, delta: float, **kwargs):
        for enemy_ent, (enemy, burning) in self.world.get_components(Enemy, Burning):
            burning.elapsed += delta

            if burning.tick_due:
                # TODO DRY take damage / delete entity
                enemy.take_damage(burning.damage)

                if enemy.is_dead:
                    self.world.delete_entity(enemy_ent)

                burning.ticks += 1


class EnemyStatusVisualEffectProcessor(esper.Processor):
    def process(self, *args, assets: Assets, **kwargs):
        for enemy_ent, (enemy, bbox, renderable) in self.world.get_components(
            Enemy, BoundingBox, Renderable
        ):
            # health bar
            health_bar_extra_renderable = renderable.extras[
                RenderableExtraKind.HealthBar
            ]

            health_bar_height = 4
            health_bar_full_width = 32
            health_bar_image = pygame.Surface(
                (health_bar_full_width, health_bar_height), pygame.SRCALPHA
            )

            health_bar_filled_width = int(
                health_bar_full_width * enemy.health_ratio / 100.0
            )
            health_bar_filled = pygame.Surface(
                (health_bar_filled_width, health_bar_height)
            )
            health_bar_filled.fill(("#ff0006"))

            health_bar_image.blit(health_bar_filled, (0, 0))

            ## positioned on top of enemy with margin
            health_bar_rect = health_bar_image.get_rect()
            health_bar_rect.bottomleft = bbox.rect.topleft
            health_bar_rect.top -= 8

            health_bar_extra_renderable.image = health_bar_image
            health_bar_extra_renderable.order = RenderableExtraOrder.Over
            health_bar_extra_renderable.rect = health_bar_rect

            # status effect bar
            status_effect_extra_renderable = renderable.extras[
                RenderableExtraKind.StatusEffectBar
            ]

            status_effect_image = pygame.Surface((80, 18), pygame.SRCALPHA)

            if self.world.has_component(enemy_ent, Burning):
                status_effect_image.blit(assets.burning_status_effect, (0, 0))

            # TODO
            # if self.world.has_component(enemy_ent, Slowed):
            #     status_effect_image.blit(assets.slowed_status_effect, (0, 0))

            ## positioned on top of enemy, with margin
            status_effect_rect = status_effect_image.get_rect()
            status_effect_rect.bottomleft = bbox.rect.topleft
            status_effect_rect.top -= 12 + health_bar_height

            status_effect_extra_renderable.image = status_effect_image
            status_effect_extra_renderable.order = RenderableExtraOrder.Over
            status_effect_extra_renderable.rect = status_effect_rect
