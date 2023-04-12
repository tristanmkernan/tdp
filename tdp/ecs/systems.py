import logging

import pygame
import pygame.constants
from pygame import Vector2, Rect

from tdp.constants import (
    MAP_HEIGHT,
    MAP_WIDTH,
    PygameCustomEventType,
)
from tdp.ecs.statsrepo import StatsRepo

from .assets import Assets
from .gui import (
    GuiElements,
    sync_research_gui,
    sync_selected_turret_gui,
    sync_turret_build_buttons_ui,
)
from .types import PlayerAction
from .components import (
    Animated,
    BoundingBox,
    Buffeted,
    Burning,
    DamagesEnemy,
    Enemy,
    Lifetime,
    PlayerInputMachine,
    PlayerResearch,
    PlayerResources,
    Poisoned,
    RemoveOnOutOfBounds,
    Shocked,
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
    create_lightning_turret,
    fire_turret,
    create_flame_turret,
    create_bullet_turret,
    create_rocket_turret,
    create_poison_turret,
    create_tornado_turret,
    kill_enemy,
    player_researching_idle,
    research_incomplete,
    spawn_commando,
    spawn_elite,
    spawn_fighter_plane,
    spawn_grunt,
    spawn_tank,
    spawn_transport_plane,
    start_research,
    sync_selected_turret_range_extra_renderable,
    track_score_event,
    turret_property_can_be_upgraded,
    upgrade_turret,
    sell_turret,
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
    VelocityAdjustmentSource,
)
from .rendering import render_composite, render_simple
from .resources import (
    player_has_resources_to_build_turret,
    player_has_resources_to_research,
    player_has_resources_to_upgrade_turret,
    subtract_resources_to_build_turret,
    subtract_resources_to_research,
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
    world.add_processor(ResearchProcessor())
    world.add_processor(PlayerResourcesProcessor())
    world.add_processor(TurretStateProcessor())
    world.add_processor(BuffetedProcessor())
    world.add_processor(BurningProcessor())
    world.add_processor(ShockedProcessor())
    world.add_processor(PoisonedProcessor())
    world.add_processor(EnemyStatusVisualEffectProcessor())
    world.add_processor(TimeToLiveProcessor())
    world.add_processor(MovementProcessor())

    world.add_processor(SpawningProcessor())
    world.add_processor(OutOfBoundsProcessor())
    world.add_processor(DamagesEnemyProcessor())
    world.add_processor(PlayerInputProcessor())
    world.add_processor(ScoreTimeTrackerProcessor())
    world.add_processor(LifetimeProcessor())
    world.add_processor(PathingProcessor())
    world.add_processor(DespawningProcessor())

    world.add_processor(AnimationProcessor())
    world.add_processor(RotationProcessor())
    world.add_processor(RenderingProcessor())


# TODO would like this in a different module
def remove_game_over_systems(world: esper.World):
    # remove spawning system
    world.remove_processor(SpawningProcessor)


def set_game_over(world: esper.World, gui_elements: GuiElements):
    remove_game_over_systems(world)

    # sync player state
    player_input_machine = world.get_component(PlayerInputMachine)[0][1]

    player_input_machine.state = PlayerInputState.GameOver

    # sync ui
    score_tracker = world.get_component(ScoreTracker)[0][1]

    gui_elements.game_over_score_label.set_text(f"Score: {score_tracker.total_score}")

    gui_elements.game_over_window.show()


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
                        kind=VelocityAdjustmentKind.Slowdown, factor=factor
                    ):
                        velocity_vector.scale_to_length(
                            velocity_vector.magnitude() * factor
                        )

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
    def process(
        self,
        *args,
        delta: float,
        stats_repo: StatsRepo,
        gui_elements: GuiElements,
        assets,
        **kwargs,
    ):
        # NOTE: only one spawn point at the moment
        spawning_ent, spawning = self.world.get_component(Spawning)[0]

        wave = spawning.current_wave

        current_step = wave.current_step

        match current_step:
            case {"kind": SpawningWaveStepKind.SpawnEnemy, "enemy_kind": enemy_kind}:
                spawning_map = {
                    EnemyKind.Grunt: spawn_grunt,
                    EnemyKind.Tank: spawn_tank,
                    EnemyKind.Elite: spawn_elite,
                    EnemyKind.Commando: spawn_commando,
                    EnemyKind.FighterPlane: spawn_fighter_plane,
                    EnemyKind.TransportPlane: spawn_transport_plane,
                }

                enemy = spawning_map[enemy_kind](
                    self.world,
                    spawning_ent,
                    level=spawning.current_wave_index,
                    assets=assets,
                    stats_repo=stats_repo,
                )

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
            collided = False

            for enemy_ent, (
                enemy,
                enemy_bbox,
            ) in self.world.get_components(Enemy, BoundingBox):
                if damaging_bbox.rect.colliderect(enemy_bbox.rect):
                    logger.debug("Damaging entity id=%d", enemy_ent)

                    collided = True

                    enemy.take_damage(damages_enemy.damage)

                    if enemy.is_dead:
                        track_score_event(self.world, ScoreEventKind.EnemyKill)

                        kill_enemy(self.world, enemy_ent)
                    elif damages_enemy.applies_effects:
                        apply_damage_effects_to_enemy(
                            self.world, damaging_ent, enemy_ent, assets=assets
                        )

                    if (
                        damages_enemy.on_collision_behavior
                        == DamagesEnemyOnCollisionBehavior.Pierce
                    ):
                        damages_enemy.pierced_count += 1

                        if damages_enemy.expired:
                            self.world.delete_entity(damaging_ent)

                            break

            if collided:
                match damages_enemy.on_collision_behavior:
                    case DamagesEnemyOnCollisionBehavior.DeleteEntity:
                        self.world.delete_entity(damaging_ent)
                    case DamagesEnemyOnCollisionBehavior.RemoveComponent:
                        self.world.remove_component(damaging_ent, DamagesEnemy)


class PlayerInputProcessor(esper.Processor):
    def process(
        self,
        *args,
        player: int,
        stats_repo: StatsRepo,
        assets: Assets,
        gui_elements: GuiElements,
        **kwargs,
    ):
        # TODO consider sorting by keydown, then keyup,
        #   in case we receive a sequence "out of order" like
        #   [W key up, W key down]
        input_events = kwargs["player_input_events"]
        player_actions: list[PlayerAction] = []

        player_input_machine = self.world.component_for_entity(
            player, PlayerInputMachine
        )
        player_research = self.world.component_for_entity(player, PlayerResearch)

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
            PlayerInputState.GameOver: {PlayerActionKind.ExitGame},
            PlayerInputState.Idle: {
                PlayerActionKind.SetTurretToBuild,
                PlayerActionKind.SelectTurret,
                PlayerActionKind.StartResearch,
            },
            PlayerInputState.SelectingTurret: {
                PlayerActionKind.SelectTurret,
                PlayerActionKind.UpgradeTurretProperty,
                PlayerActionKind.SetTurretToBuild,
                PlayerActionKind.SellTurret,
                PlayerActionKind.StartResearch,
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
                case {"kind": PlayerActionKind.ExitGame}:
                    pygame.event.post(
                        pygame.event.Event(PygameCustomEventType.ChangeScene)
                    )
                case {
                    "kind": PlayerActionKind.StartResearch,
                    "research_kind": research_kind,
                }:
                    if (
                        player_has_resources_to_research(
                            self.world, player, research_kind, stats_repo
                        )
                        and research_incomplete(self.world, player, research_kind)
                        and player_researching_idle(self.world, player)
                    ):
                        start_research(self.world, player, research_kind, stats_repo)

                        subtract_resources_to_research(
                            self.world, player, research_kind, stats_repo
                        )

                case {"kind": PlayerActionKind.SelectTurret, "ent": ent}:
                    # toggle selected turret
                    if ent == player_input_machine.selected_turret:
                        player_input_machine.state = PlayerInputState.Idle
                        player_input_machine.selected_turret = None
                    else:
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
                        player_research,
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

                case {"kind": PlayerActionKind.SellTurret}:
                    sell_turret(
                        self.world, player_input_machine.selected_turret, assets=assets
                    )

                    player_input_machine.state = PlayerInputState.Idle
                    player_input_machine.selected_turret = None

                    changed_selected_turret = True

                case {
                    "kind": PlayerActionKind.SetTurretToBuild,
                    "turret_kind": turret_kind,
                }:
                    if player_has_resources_to_build_turret(
                        self.world, turret_kind, stats_repo
                    ):
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

                    turret_creator_map = {
                        TurretKind.Flame: create_flame_turret,
                        TurretKind.Bullet: create_bullet_turret,
                        TurretKind.Rocket: create_rocket_turret,
                        TurretKind.Frost: create_frost_turret,
                        TurretKind.Lightning: create_lightning_turret,
                        TurretKind.Poison: create_poison_turret,
                        TurretKind.Tornado: create_tornado_turret,
                    }

                    new_turret_ent = turret_creator_map[
                        player_input_machine.turret_to_build
                    ](self.world, ent, assets=assets, stats_repo=stats_repo)

                    subtract_resources_to_build_turret(
                        self.world, player_input_machine.turret_to_build, stats_repo
                    )

                    player_input_machine.state = PlayerInputState.SelectingTurret
                    player_input_machine.turret_to_build = None
                    player_input_machine.selected_turret = new_turret_ent

                    changed_turret_to_build = True
                    changed_selected_turret = True

        if changed_turret_to_build:
            sync_turret_build_buttons_ui(self.world, player, gui_elements)

        if changed_selected_turret:
            # sync range ring extra renderable for turret
            sync_selected_turret_range_extra_renderable(
                self.world,
                player_input_machine.selected_turret,
            )

            if player_input_machine.selected_turret:
                # update selected turret ui
                sync_selected_turret_gui(
                    self.world, player_input_machine.selected_turret, gui_elements
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

            vec = (target_vertex - Vector2(*bbox.rect.center)).normalize()

            vec.scale_to_length(vel.vec.magnitude())

            vel.vec = vec

            # orient towards the next vertex
            bbox.rotation = vec


class DespawningProcessor(esper.Processor):
    def process(self, *args, delta: float, gui_elements: GuiElements, **kwargs):
        # TODO clean this up
        # could be more efficient than N^2
        # would be cool to have intersection done once per frame
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

                    # game over
                    set_game_over(self.world, gui_elements)


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
                    elif turret_machine.rotates:
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

                        if turret_machine.rotates:
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

                        if turret_machine.rotates:
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
                    track_score_event(self.world, ScoreEventKind.EnemyKill)

                    kill_enemy(self.world, enemy_ent)

                burning.ticks += 1

            if burning.expired:
                self.world.remove_component(enemy_ent, Burning)


class PoisonedProcessor(esper.Processor):
    def process(self, *args, delta: float, **kwargs):
        for enemy_ent, (enemy, poisoned) in self.world.get_components(Enemy, Poisoned):
            poisoned.elapsed += delta

            if poisoned.tick_due:
                # TODO DRY take damage / delete entity
                enemy.take_damage(poisoned.damage)

                if enemy.is_dead:
                    track_score_event(self.world, ScoreEventKind.EnemyKill)

                    kill_enemy(self.world, enemy_ent)

                poisoned.ticks += 1

            if poisoned.expired:
                self.world.remove_component(enemy_ent, Poisoned)


class ShockedProcessor(esper.Processor):
    def process(self, *args, delta: float, **kwargs):
        for enemy_ent, (enemy, shocked) in self.world.get_components(Enemy, Shocked):
            shocked.elapsed += delta

            if shocked.expired:
                self.world.remove_component(enemy_ent, Shocked)


class BuffetedProcessor(esper.Processor):
    def process(self, *args, delta: float, **kwargs):
        for enemy_ent, (enemy, buffeted, vel) in self.world.get_components(
            Enemy, Buffeted, Velocity
        ):
            # reset velocity adjustment
            vel.adjustments[VelocityAdjustmentSource.Buffeted] = VelocityAdjustment(
                VelocityAdjustmentKind.Slowdown, duration=500.0, factor=0.5
            )

            buffeted.elapsed += delta

            if buffeted.tick_due:
                # TODO DRY take damage / delete entity
                enemy.take_damage(buffeted.damage)

                if enemy.is_dead:
                    track_score_event(self.world, ScoreEventKind.EnemyKill)

                    kill_enemy(self.world, enemy_ent)

                buffeted.ticks += 1

            if buffeted.expired:
                self.world.remove_component(enemy_ent, Buffeted)


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

            status_effect_image = pygame.Surface((80, 14), pygame.SRCALPHA)

            if self.world.has_component(enemy_ent, Burning):
                status_effect_image.blit(assets.burning_status_effect, (0, 0))

            if self.world.has_component(enemy_ent, Poisoned):
                status_effect_image.blit(assets.poisoned_status_effect, (14, 0))

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


class ResearchProcessor(esper.Processor):
    def process(
        self, *args, gui_elements: GuiElements, player: int, delta: float, **kwargs
    ):
        player_research = self.world.component_for_entity(player, PlayerResearch)

        if player_research.research_in_progress is not None:
            player_research.elapsed += delta

            if player_research.research_complete:
                player_research.completed.add(player_research.research_in_progress)

                player_research.reset_in_progress()

        sync_research_gui(self.world, player, gui_elements)
