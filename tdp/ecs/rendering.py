from collections import defaultdict
import pygame

from tdp.ecs.enums import RenderableExtraOrder

from .components import BoundingBox, Renderable, RenderableExtra


def render_simple(screen: pygame.Surface, renderable: Renderable, bbox: BoundingBox):
    screen.blit(renderable.image, bbox.rect.topleft)


def render_composite(screen: pygame.Surface, renderable: Renderable, bbox: BoundingBox):
    order_map: defaultdict[RenderableExtraOrder, list[RenderableExtra]] = defaultdict(
        list
    )

    for extra in renderable.extras.values():
        order_map[extra.order].append(extra)

    # draw underneath first
    for extra in order_map[RenderableExtraOrder.Under]:
        screen.blit(extra.image, extra.rect.topleft)

    # draw core object
    screen.blit(renderable.image, bbox.rect.topleft)

    # draw over last
    for extra in order_map[RenderableExtraOrder.Over]:
        screen.blit(extra.image, extra.rect.topleft)
