import enum

import pygame

MAP_WIDTH, MAP_HEIGHT = 960, 960

GUI_X_OFFSET, GUI_Y_OFFSET = 960, 0
GUI_WIDTH, GUI_HEIGHT = 256, 960

SCREEN_WIDTH, SCREEN_HEIGHT = 960 + GUI_WIDTH, 960

PLAYER_STARTING_MONEY = 75

MAX_TURRET_PROPERTY_UPGRADE_LEVEL = 10


class PygameCustomEventType(enum.IntEnum):
    ChangeScene = pygame.event.custom_type()
