from .components import SpawningWave
from .enums import EnemyKind


def generate_waves() -> list[SpawningWave]:
    return [
        SpawningWave(wave=[EnemyKind.Grunt for _ in range(10)]),
        SpawningWave(wave=[EnemyKind.Tank for _ in range(10)]),
    ]
