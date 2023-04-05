import dataclasses
import logging

import pygame

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Assets:
    grunt: pygame.Surface
    elite: pygame.Surface
    commando: pygame.Surface
    tank: pygame.Surface

    turret_build_zone: pygame.Surface

    bullet_turret: pygame.Surface
    bullet_turret__firing: pygame.Surface

    flame_turret: pygame.Surface
    flame_particle: pygame.Surface

    frost_turret: pygame.Surface
    frost_missile_frames: list[pygame.Surface]
    frost_missile_explosion_frames: list[pygame.Surface]

    lightning_turret: pygame.Surface
    lightning_strike_frames: list[pygame.Surface]

    rocket_turret: pygame.Surface
    rocket_turret__reloading: pygame.Surface
    rocket_missile: pygame.Surface
    rocket_missile_explosion: pygame.Surface

    burning_status_effect: pygame.Surface


def load_assets() -> Assets:
    return Assets(
        grunt=pygame.image.load("assets/enemies/grunt.png"),
        elite=pygame.image.load("assets/enemies/elite.png"),
        commando=pygame.image.load("assets/enemies/commando.png"),
        tank=pygame.image.load("assets/enemies/tank.png"),
        turret_build_zone=pygame.image.load("assets/turrets/buildzone.png"),
        bullet_turret=pygame.image.load("assets/turrets/mach1.png"),
        bullet_turret__firing=pygame.image.load("assets/turrets/mach1--firing.png"),
        flame_turret=pygame.image.load("assets/turrets/flame1.png"),
        flame_particle=pygame.image.load("assets/turrets/flame-particle.png"),
        lightning_turret=pygame.image.load("assets/turrets/lightning1.png"),
        lightning_strike_frames=load_sheet_frames(
            "assets/turrets/lightning-strike-sheet.png", (128, 128)
        ),
        frost_turret=pygame.image.load("assets/turrets/frost1.png"),
        frost_missile_frames=load_sheet_frames(
            "assets/turrets/frost-missile-sheet.png", (64, 64)
        ),
        frost_missile_explosion_frames=load_sheet_frames(
            "assets/turrets/frost-missile-explosion-sheet.png", (128, 128)
        ),
        rocket_turret=pygame.image.load("assets/turrets/rocket1.png"),
        rocket_turret__reloading=pygame.image.load(
            "assets/turrets/rocket1--reloading.png"
        ),
        rocket_missile=pygame.image.load("assets/turrets/rocket-missile.png"),
        rocket_missile_explosion=pygame.image.load(
            "assets/turrets/rocket-missile-explosion.png"
        ),
        burning_status_effect=pygame.image.load("assets/enemies/status/burning.png"),
    )


def load_sheet_frames(
    filename: str, frame_dims: tuple[int, int]
) -> list[pygame.Surface]:
    sheet = pygame.image.load(filename)

    sheet_rect = sheet.get_rect()

    frames: list[pygame.Surface] = []

    x, y = 0, 0

    while y < sheet_rect.height:
        frame = pygame.Surface(frame_dims, pygame.SRCALPHA)

        frame_rect = pygame.Rect((x, y), frame_dims)

        frame.blit(sheet, (0, 0), frame_rect)

        frames.append(frame)

        x += frame_dims[0]

        if x >= sheet_rect.width:
            # next row
            x = 0
            y += frame_dims[1]

    logger.debug("Loaded %d frames from sheet %s", len(frames), filename)

    return frames
