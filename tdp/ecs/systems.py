import logging

import pygame
import pygame.constants
from pygame import Vector2

from tdp.constants import SCREEN_HEIGHT, SCREEN_WIDTH

from .types import PlayerAction
from .components import (
    BoundingBox,
    Bullet,
    Enemy,
    Lifetime,
    PlayerKeyInput,
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
    create_turret,
    create_bullet,
    spawn_enemy,
    track_score_event,
)
from .enums import (
    ScoreEventKind,
    InputEventKind,
    PlayerActionKind,
    TurretState,
)
from .util import get_player_action_for_click, get_closest_enemy
from . import esper

logger = logging.getLogger(__name__)


def add_systems(world: esper.World):
    world.add_processor(MovementProcessor())
    world.add_processor(RotationProcessor())
    world.add_processor(SpawningProcessor())
    world.add_processor(BulletProcessor())
    world.add_processor(PlayerInputProcessor())
    #    world.add_processor(ScoreTimeTrackerProcessor())
    world.add_processor(LifetimeProcessor())
    world.add_processor(PathingProcessor())
    world.add_processor(DespawningProcessor())
    world.add_processor(TurretStateProcessor())

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
    def process(self, *args, delta, **kwargs):
        for ent, spawning in self.world.get_component(Spawning):
            spawning.elapsed += delta

            if spawning.elapsed > spawning.every:
                enemy = spawn_enemy(self.world, ent)

                logger.info("Spawned new enemy id=%d", enemy)

                spawning.elapsed = 0.0


class RenderingProcessor(esper.Processor):
    def __init__(self) -> None:
        super().__init__()

        self.font = pygame.font.SysFont("Comic", 40)

    def process(self, *args, **kwargs):
        show_fps = kwargs["show_fps"]
        screen = kwargs["screen"]
        clock = kwargs["clock"]
        debug = kwargs["debug"]

        screen.fill((255, 255, 255))

        renderables = self.world.get_components(Renderable, BoundingBox)

        # sort by z-index to display in correct order
        renderables = sorted(renderables, key=lambda item: item[1][0].order)

        for _, (renderable, bbox) in renderables:
            screen.blit(renderable.image, bbox.rect.topleft)

            # render bounding box in debug mode
            if debug:
                pygame.draw.rect(screen, (0, 0, 0), bbox.rect, 2)

        # _, score_tracker = self.world.get_component(ScoreTracker)[0]
        # _, (_, bullet_ammo) = self.world.get_components(PlayerShip, BulletAmmo)[0]

        # time_str = f"Time {score_tracker.scores[ScoreEventKind.Time]:.1f}"
        # screen.blit(
        #     self.font.render(time_str, True, pygame.Color(0, 0, 0)),
        #     (SCREEN_WIDTH - 150, 0),
        # )

        # kills_str = f"Kills {score_tracker.scores[ScoreEventKind.EnemyKill]}"
        # screen.blit(
        #     self.font.render(kills_str, True, pygame.Color(0, 0, 0)),
        #     (SCREEN_WIDTH - 150, 24),
        # )

        # ammo_str = f"Ammo {bullet_ammo.count}"
        # screen.blit(
        #     self.font.render(ammo_str, True, pygame.Color(0, 0, 0)),
        #     (SCREEN_WIDTH - 150, 48),
        # )

        if show_fps:
            fps_str = f"{clock.get_fps():.1f}"

            fps_overlay = self.font.render(fps_str, True, pygame.Color(0, 0, 0))

            screen.blit(fps_overlay, (0, 0))

        pygame.display.flip()


class BulletProcessor(esper.Processor):
    def process(self, *args, **kwargs):
        for bullet_ent, (bullet, bullet_bbox) in self.world.get_components(
            Bullet, BoundingBox
        ):
            for enemy_ent, (
                enemy,
                enemy_bbox,
            ) in self.world.get_components(Enemy, BoundingBox):
                if bullet_bbox.rect.colliderect(enemy_bbox.rect):
                    logger.info("Destroying entity id=%d", enemy_ent)

                    track_score_event(self.world, ScoreEventKind.EnemyKill)

                    ## destroy enemy and self
                    self.world.delete_entity(enemy_ent)
                    self.world.delete_entity(bullet_ent)

                    break

            # cleanup: when bullet leaves world boundaries
            if (
                bullet_bbox.rect.x <= 0
                or bullet_bbox.rect.x >= SCREEN_WIDTH
                or bullet_bbox.rect.y <= 0
                or bullet_bbox.rect.y >= SCREEN_HEIGHT
            ):
                logger.info("Bullet out of bounds id=%d", bullet_ent)
                self.world.delete_entity(bullet_ent)


class PlayerInputProcessor(esper.Processor):
    def process(self, *args, **kwargs):
        # TODO consider sorting by keydown, then keyup,
        #   in case we receive a sequence "out of order" like
        #   [W key up, W key down]
        input_events = kwargs["player_input_events"]
        player_actions: list[PlayerAction] = []

        _, player_key_input = self.world.get_component(PlayerKeyInput)[0]

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

        for action in player_actions:
            match action:
                case {"kind": PlayerActionKind.SelectTurretBuildZone, "ent": ent}:
                    # for now, let's just build a turret here
                    create_turret(self.world, ent)


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
    def process(self, *args, delta, **kwargs):
        for turret_ent, (turret_machine, turret_bbox) in self.world.get_components(
            TurretMachine, BoundingBox
        ):
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

                        # spawn bullet
                        bullet = create_bullet(self.world, turret_ent, closest_enemy)

                        logger.info("Spawned bullet id=%d", bullet)

                        turret_machine.elapsed = 0.0

                        # transition to tracking
                        turret_machine.state = TurretState.Tracking

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
