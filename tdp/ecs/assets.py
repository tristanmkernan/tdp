import dataclasses

import pygame


@dataclasses.dataclass
class Assets:
    grunt: pygame.Surface
    tank: pygame.Surface

    bullet_turret: pygame.Surface
    bullet_turret__firing: pygame.Surface

    flame_turret: pygame.Surface
    flame_particle: pygame.Surface

    rocket_turret: pygame.Surface
    rocket_turret__reloading: pygame.Surface
    rocket_missile: pygame.Surface
    rocket_missile_explosion: pygame.Surface


def load_assets() -> Assets:
    return Assets(
        grunt=pygame.image.load("assets/enemies/grunt.png"),
        tank=pygame.image.load("assets/enemies/tank.png"),
        bullet_turret=pygame.image.load("assets/turrets/mach1.png"),
        bullet_turret__firing=pygame.image.load("assets/turrets/mach1--firing.png"),
        flame_turret=pygame.image.load("assets/turrets/flame1.png"),
        flame_particle=pygame.image.load("assets/turrets/flame-particle.png"),
        rocket_turret=pygame.image.load("assets/turrets/rocket1.png"),
        rocket_turret__reloading=pygame.image.load(
            "assets/turrets/rocket1--reloading.png"
        ),
        rocket_missile=pygame.image.load("assets/turrets/rocket-missile.png"),
        rocket_missile_explosion=pygame.image.load(
            "assets/turrets/rocket-missile-explosion.png"
        ),
    )
