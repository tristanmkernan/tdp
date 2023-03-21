import logging

from pygame import Rect, Vector2
from pytmx.util_pygame import load_pygame

TILE_WIDTH, TILE_HEIGHT = 64, 64

from .components import (
    Despawning,
    PathGraph,
    Renderable,
    BoundingBox,
    Spawning,
    TurretBuildZone,
)
from .enums import RenderableOrder, ObjectKind

from . import esper

logger = logging.getLogger(__name__)


def load_map(world: esper.World):
    # TODO parameterize file
    tiled_map = load_pygame("assets/maps/map1.tmx")

    # base layer
    base_layer = tiled_map.get_layer_by_name("Base")

    for x, y, image in base_layer.tiles():
        world.create_entity(
            Renderable(
                image=image,
                order=RenderableOrder.Base,
            ),
            BoundingBox(rect=Rect(x * TILE_WIDTH, y * TILE_HEIGHT, 64, 64)),
        )

    # environment layer
    environment_layer = tiled_map.get_layer_by_name("Environment")

    for x, y, image in environment_layer.tiles():
        world.create_entity(
            Renderable(
                image=image,
                order=RenderableOrder.Environment,
            ),
            BoundingBox(rect=Rect(x * TILE_WIDTH, y * TILE_HEIGHT, 64, 64)),
        )

    # object layer
    object_layer = tiled_map.get_layer_by_name("Objects")

    ## turret spawns
    turret_spawns = [
        obj for obj in object_layer if obj.type == ObjectKind.TurretBuildZone
    ]

    for obj in turret_spawns:
        world.create_entity(
            Renderable(
                image=obj.image,
                order=RenderableOrder.Objects,
            ),
            BoundingBox(rect=Rect(obj.x, obj.y, obj.width, obj.height)),
            TurretBuildZone(),
        )

    ## pathing
    pathings = [obj for obj in object_layer if obj.type == ObjectKind.Path]

    start_obj = next(obj for obj in pathings if obj.name == "PathStart")
    end_obj = next(obj for obj in pathings if obj.name == "PathEnd")

    end_bbox = BoundingBox(
        rect=Rect(end_obj.x, end_obj.y, end_obj.width, end_obj.height)
    )

    world.create_entity(Despawning(), end_bbox)

    ### vertex objs are ordered by index
    ### TODO build graph dynamically from vertex obj -> next property
    vertex_objs = [obj for obj in pathings if obj not in (start_obj, end_obj)]

    vertices: list[Vector2] = [
        Vector2(obj.x, obj.y)
        for obj in sorted(vertex_objs, key=lambda v: v.properties["index"])
    ]

    vertices.append(Vector2(end_bbox.rect.centerx, end_bbox.rect.centery))

    world.create_entity(
        Spawning(rate=1.0 / 5_000.0),
        BoundingBox(rect=Rect(start_obj.x, start_obj.y, 0, 0)),
        PathGraph(vertices=vertices),
    )
