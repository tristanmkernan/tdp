import logging

import pygame
import pygame.constants
from pygame import Vector2, Rect

from tdp.constants import MAP_HEIGHT, MAP_WIDTH

from .assets import Assets
from .gui import GuiElements
from .types import PlayerAction
from .components import (
    BoundingBox,
    DamagesEnemy,
    Enemy,
    Lifetime,
    PlayerInputMachine,
    PlayerResources,
    TurretMachine,
    Velocity,
    Spawning,
    Renderable,
    ScoreTracker,
    UnitPathing,
    Despawnable,
    Despawning,
)
from .entities import (
    fire_turret,
    create_flame_turret,
    create_bullet_turret,
    kill_enemy,
    spawn_grunt,
    spawn_tank,
    track_score_event,
)
from .enums import (
    EnemyKind,
    PlayerInputState,
    ScoreEventKind,
    InputEventKind,
    PlayerActionKind,
    TurretKind,
    TurretState,
)
from .resources import (
    player_has_resources_to_build_turret,
    subtract_resources_to_build_turret,
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
    world.add_processor(MovementProcessor())
    world.add_processor(RotationProcessor())
    world.add_processor(SpawningProcessor())
    world.add_processor(OutOfBoundsProcessor())
    world.add_processor(DamagesEnemyProcessor())
    world.add_processor(PlayerInputProcessor())
    #    world.add_processor(ScoreTimeTrackerProcessor())
    world.add_processor(LifetimeProcessor())
    world.add_processor(PathingProcessor())
    world.add_processor(DespawningProcessor())

    world.add_processor(RenderingProcessor())


class MovementProcessor(esper.Processor):
    def process(self, *args, delta, **kwargs):
        # update rotation
        # for _, (rot, pos) in self.world.get_components(Rotation, Position):
        #     pos.rotation += rot.speed * delta
        #     pos.normalize_rotation()

        # update position
        for _, (vel, bbox) in self.world.get_components(Velocity, BoundingBox):
            bbox.rect.centerx += vel.vec.x * delta
            bbox.rect.centery += vel.vec.y * delta


class SpawningProcessor(esper.Processor):
    def process(self, *args, delta, gui_elements: GuiElements, assets, **kwargs):
        # NOTE: only one spawn point at the moment
        spawning_ent, spawning = self.world.get_component(Spawning)[0]

        wave = spawning.current_wave

        spawning.elapsed += delta

        # spawn, if necessary
        if spawning.elapsed > spawning.every:
            enemy_kind = wave.get_and_advance()

            if wave.over:
                spawning.advance()

            match enemy_kind:
                case EnemyKind.Grunt:
                    enemy = spawn_grunt(self.world, spawning_ent, assets=assets)
                case EnemyKind.Tank:
                    enemy = spawn_tank(self.world, spawning_ent, assets=assets)

            logger.info("Spawned new enemy id=%d", enemy)

            spawning.elapsed = 0.0

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
            screen.blit(renderable.image, bbox.rect.topleft)

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
        # TODO create OutOfBounds component?
        # cleanup: when bullet leaves world boundaries
        screen_rect = Rect((0, 0), (MAP_WIDTH, MAP_HEIGHT))
        for damaging_ent, (damages_enemy, damaging_bbox) in self.world.get_components(
            DamagesEnemy, BoundingBox
        ):
            if not damaging_bbox.rect.colliderect(screen_rect):
                logger.info("Entity out of bounds id=%d", damaging_ent)
                self.world.delete_entity(damaging_ent)


class DamagesEnemyProcessor(esper.Processor):
    def process(self, *args, **kwargs):
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

                    self.world.delete_entity(damaging_ent)

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
            PlayerInputState.Idle: {PlayerActionKind.SetTurretToBuild},
            PlayerInputState.BuildingTurret: {
                PlayerActionKind.ClearTurretToBuild,
                PlayerActionKind.SetTurretToBuild,
                PlayerActionKind.SelectTurretBuildZone,
            },
        }

        for action in player_actions:
            if not action["kind"] in acceptable_actions[player_input_machine.state]:
                continue

            match action:
                case {
                    "kind": PlayerActionKind.SetTurretToBuild,
                    "turret_kind": turret_kind,
                }:
                    if player_has_resources_to_build_turret(self.world, turret_kind):
                        player_input_machine.turret_to_build = turret_kind
                        player_input_machine.state = PlayerInputState.BuildingTurret

                case {"kind": PlayerActionKind.ClearTurretToBuild}:
                    player_input_machine.turret_to_build = None
                    player_input_machine.state = PlayerInputState.Idle

                case {"kind": PlayerActionKind.SelectTurretBuildZone, "ent": ent}:
                    # for now, let's just build a turret here
                    # TODO also could have hover state, building time, so on
                    match player_input_machine.turret_to_build:
                        case TurretKind.Flame:
                            create_flame_turret(self.world, ent, assets=assets)
                        case TurretKind.Bullet:
                            create_bullet_turret(self.world, ent, assets=assets)
                        case TurretKind.Rocket:
                            create_rocket_turret(self.world, ent, assets=assets)

                    subtract_resources_to_build_turret(
                        self.world, player_input_machine.turret_to_build
                    )

                    player_input_machine.turret_to_build = None
                    player_input_machine.state = PlayerInputState.Idle

        # TODO synchronize UI with state
        # maybe add a border (or other visual effect) to the selected turret button
        turret_gui_element_map = {
            TurretKind.Bullet: gui_elements.basic_turret_build_button,
            TurretKind.Flame: gui_elements.flame_turret_build_button,
            TurretKind.Rocket: gui_elements.rocket_turret_build_button,
        }

        match player_input_machine.state:
            case PlayerInputState.Idle:
                # reset button classes
                for gui_button in turret_gui_element_map.values():
                    # TODO
                    # gui_button.class_ids = ["@turret-build-button--selected"]
                    gui_button.enable()
            case PlayerInputState.BuildingTurret:
                # reset button classes
                for gui_button in turret_gui_element_map.values():
                    # TODO
                    # gui_button.class_ids = ["@turret-build-button--selected"]
                    gui_button.enable()

                if gui_button := turret_gui_element_map.get(
                    player_input_machine.turret_to_build
                ):
                    # TODO
                    # gui_button.class_ids = ["@turret-build-button--selected"]
                    gui_button.disable()


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
                case (TurretKind.Bullet, _):
                    renderable.image = renderable.original_image = assets.bullet_turret
                case (TurretKind.Flame, _):
                    renderable.image = renderable.original_image = assets.flame_turret


class PlayerResourcesProcessor(esper.Processor):
    def process(self, *args, gui_elements: GuiElements, **kwargs):
        # update the resources label with the current player resources
        player_resources = self.world.get_component(PlayerResources)[0][1]

        gui_elements.resources_label.set_text(f"Money: ${player_resources.money}")
