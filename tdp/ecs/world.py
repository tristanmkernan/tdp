from . import esper

from .entities import (
    create_player_resources,
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

    # TODO player components should be attached to a player entity
    create_scoreboard(world)

    create_player_input(world)

    create_player_resources(world)

    return world
