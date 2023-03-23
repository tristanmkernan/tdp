import dataclasses

import pygame


@dataclasses.dataclass
class Assets:
    grunt: pygame.Surface
    tank: pygame.Surface

    turret: pygame.Surface
    turret__firing: pygame.Surface


def load_assets() -> Assets:
    return Assets(
        grunt=pygame.image.load("assets/enemies/grunt.png"),
        tank=pygame.image.load("assets/enemies/tank.png"),
        turret=pygame.image.load("assets/turrets/mach1.png"),
        turret__firing=pygame.image.load("assets/turrets/mach1--firing.png"),
    )
