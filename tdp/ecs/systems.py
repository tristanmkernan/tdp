import logging

import pygame
import pygame.constants
from pygame import Vector2

from tdp.constants import SCREEN_HEIGHT, SCREEN_WIDTH


from .components import (
    BoundingBox,
    Bullet,
    Lifetime,
    PlayerKeyInput,
    Velocity,
    Spawning,
    Renderable,
    ScoreTracker,
    UnitPathing,
    Despawnable,
    Despawning,
)
from .entities import (
    create_bullet,
    set_player_acceleration,
    set_player_rotating_left,
    set_player_rotating_right,
    spawn_enemy,
    track_score_event,
)
from .enums import RenderableKind, ScoreEventKind, InputEventKind, PlayerActionKind
from . import esper

logger = logging.getLogger(__name__)


def add_systems(world: esper.World):
    world.add_processor(MovementProcessor())
    world.add_processor(RenderingProcessor())
    world.add_processor(SpawningProcessor())
    #    world.add_processor(BulletProcessor())
    world.add_processor(PlayerInputProcessor())
    #    world.add_processor(ScoreTimeTrackerProcessor())
    #    world.add_processor(BulletAmmoProcessor())
    #    world.add_processor(PlayerMovementVisualEffectProcessor())
    world.add_processor(LifetimeProcessor())
    world.add_processor(PathingProcessor())
    world.add_processor(DespawningProcessor())


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

        screen.fill((255, 255, 255))

        renderables = self.world.get_components(Renderable, BoundingBox)

        # sort by z-index to display in correct order
        renderables = sorted(renderables, key=lambda item: item[1][0].order)

        for _, (renderable, bbox) in renderables:
            screen.blit(renderable.image, bbox.rect.topleft)

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


class BulletAmmoProcessor(esper.Processor):
    def process(self, *args, delta, **kwargs):
        for ent, (player_ship, bullet_ammo) in self.world.get_components(
            PlayerShip, BulletAmmo
        ):
            bullet_ammo.elapsed = min(
                bullet_ammo.elapsed + delta, bullet_ammo.every + delta
            )

            if not bullet_ammo.full and bullet_ammo.elapsed > bullet_ammo.every:
                bullet_ammo.count = min(bullet_ammo.count + 1, bullet_ammo.max)

                bullet_ammo.elapsed = 0.0


class BulletProcessor(esper.Processor):
    def process(self, *args, **kwargs):
        # TODO clean this up
        # could be more efficient than N^2

        for ent, (bullet, collidable, pos) in self.world.get_components(
            Bullet, Collidable, Position
        ):
            for other_ent, (
                asteroid,
                other_collidable,
                other_pos,
            ) in self.world.get_components(Asteroid, Collidable, Position):
                if check_collision(pos, collidable, other_pos, other_collidable):
                    logger.info("Destroying entity id=%d", other_ent)

                    track_score_event(self.world, ScoreEventKind.EnemyKill)

                    ## destroy enemy and self
                    self.world.delete_entity(other_ent)
                    self.world.delete_entity(ent)

                    break

            # cleanup: when bullet leaves world boundaries
            if (
                pos.x <= 0
                or pos.x >= SCREEN_WIDTH
                or pos.y <= 0
                or pos.y >= SCREEN_HEIGHT
            ):
                logger.info("Bullet out of bounds id=%d", ent)
                self.world.delete_entity(ent)


class PlayerInputProcessor(esper.Processor):
    def process(self, *args, **kwargs):
        # TODO consider sorting by keydown, then keyup,
        #   in case we receive a sequence "out of order" like
        #   [W key up, W key down]
        input_events = kwargs["player_input_events"]
        player_actions = []

        _, player_key_input = self.world.get_component(PlayerKeyInput)[0]

        for input_event in input_events:
            logger.debug(
                "Processing player input event kind=%d key=%d",
                input_event["kind"],
                input_event["key"],
            )

            match input_event:
                case {"kind": InputEventKind.KeyUp, "key": key}:
                    player_key_input.keydowns.discard(key)

                    match key:
                        case pygame.constants.K_w:
                            player_actions.append(PlayerActionKind.StopAccelerating)
                        case pygame.constants.K_s:
                            player_actions.append(PlayerActionKind.StopDecelerating)
                        case pygame.constants.K_a:
                            player_actions.append(PlayerActionKind.StopRotateLeft)
                        case pygame.constants.K_d:
                            player_actions.append(PlayerActionKind.StopRotateRight)
                        case pygame.constants.K_SPACE:
                            player_actions.append(PlayerActionKind.Fire)
                case {"kind": InputEventKind.KeyDown, "key": key}:
                    player_key_input.keydowns.add(key)

        # keydowns are updated every frame
        # e.g. to accelerate in rotated direction
        for key in player_key_input.keydowns:
            match key:
                case pygame.constants.K_w:
                    player_actions.append(PlayerActionKind.Accelerate)
                case pygame.constants.K_s:
                    player_actions.append(PlayerActionKind.Decelerate)
                case pygame.constants.K_a:
                    player_actions.append(PlayerActionKind.RotateLeft)
                case pygame.constants.K_d:
                    player_actions.append(PlayerActionKind.RotateRight)

        for action in player_actions:
            match action:
                case PlayerActionKind.Accelerate:
                    # could add/remove acceleration component instead of modifying
                    set_player_acceleration(self.world, forward=True)
                case PlayerActionKind.StopAccelerating:
                    set_player_acceleration(self.world, unset=True)
                case PlayerActionKind.Decelerate:
                    set_player_acceleration(self.world, forward=False)
                case PlayerActionKind.StopDecelerating:
                    set_player_acceleration(self.world, unset=True)
                case PlayerActionKind.Fire:
                    create_bullet(self.world)
                case PlayerActionKind.RotateLeft:
                    set_player_rotating_left(self.world, True)
                case PlayerActionKind.StopRotateLeft:
                    set_player_rotating_left(self.world, False)
                case PlayerActionKind.RotateRight:
                    set_player_rotating_right(self.world, True)
                case PlayerActionKind.StopRotateRight:
                    set_player_rotating_right(self.world, False)


class ScoreTimeTrackerProcessor(esper.Processor):
    def process(self, *args, delta, **kwargs):
        for _, score_tracker in self.world.get_component(ScoreTracker):
            score_tracker.scores[ScoreEventKind.Time] += delta / 1_000.0


class PlayerMovementVisualEffectProcessor(esper.Processor):
    elapsed = 0.0

    def process(self, *args, delta, **kwargs):
        self.elapsed += delta

        _, (_, pos, vel) = self.world.get_components(PlayerShip, Position, Velocity)[0]

        # spawn new visual effect
        if self.elapsed > 250.0 and vel.magnitude > 0.20:
            logger.debug("Spawning movement visual effect")

            self.world.create_entity(
                Position(x=pos.x, y=pos.y),
                Lifetime(remaining=2.0 * 1_000.0),
                Renderable(kind=RenderableKind.Circle, color=(125, 125, 125), radius=3),
            )

            self.elapsed = 0.0


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
            vel.vec = (target_vertex - Vector2(*bbox.rect.center)).normalize() * 0.2


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
