from . import esper

from .map import load_map
from .systems import add_systems


def build_world(map_name: str) -> esper.World:
    world = esper.World()

    # initialize systems
    add_systems(world)

    # add entities
    load_map(world, map_name)

    return world
