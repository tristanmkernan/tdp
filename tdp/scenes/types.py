from abc import ABC, abstractmethod
from typing import NotRequired, TypedDict


import pygame
import pygame_gui


from .enums import SceneEventKind


class SceneEvent(TypedDict):
    kind: SceneEventKind

    to: NotRequired["Scene"]
    map: NotRequired[str]


class Scene(ABC):
    def __init__(
        self,
        screen: pygame.Surface,
        gui_manager: pygame_gui.UIManager,
        clock: pygame.time.Clock,
        **kwargs
    ) -> None:
        self.screen = screen
        self.gui_manager = gui_manager
        self.clock = clock

        self.setup()

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def run(self) -> SceneEvent:
        pass

    @abstractmethod
    def cleanup(self):
        pass
