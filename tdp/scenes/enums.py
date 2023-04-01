import enum


class SceneKind(enum.StrEnum):
    Main = "main"
    Game = "game"


class SceneEventKind(enum.IntEnum):
    ChangeScene = enum.auto()
    Quit = enum.auto()
