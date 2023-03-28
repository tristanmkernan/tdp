import enum


class SceneKind(enum.IntEnum):
    Main = enum.auto()
    Game = enum.auto()


class SceneEventKind(enum.IntEnum):
    ChangeScene = enum.auto()
    Quit = enum.auto()
