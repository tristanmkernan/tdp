from . import esper

from .entities import (
    create_scoreboard,
    create_player_input,
)
from .map import load_map
from .systems import add_systems


def build_world() -> esper.World:
    world = esper.World()

    # initialize systems
    add_systems(world)

    # add entities
    load_map(world)

    create_scoreboard(world)

    create_player_input(world)

    return world
