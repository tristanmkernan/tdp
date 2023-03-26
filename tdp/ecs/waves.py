from .components import SpawningWave
from .enums import EnemyKind, SpawningWaveStepKind
from .types import SpawningWaveStep


# L: long wait
# M: medium wait
# S: short wait
# G: grunt
# T: tank
# P: plane

SHORT_WAIT = 1000.0
MEDIUM_WAIT = SHORT_WAIT * 2.5
LONG_WAIT = SHORT_WAIT * 5.0

# TODO more waves
raw_waves = """
LGLGLGLGLGLGLGLGL
LGMGMGMGMGMGMGMGL
LGSGSGSGSGSGSGSGL
LTSGLTSGLTSGLTSGL
"""


def generate_waves() -> list[SpawningWave]:
    return parse_waves(raw_waves)


def parse_waves(wave_conf: str) -> list[SpawningWave]:
    wave_step_map: dict[str, SpawningWaveStep] = {
        "L": {"kind": SpawningWaveStepKind.Wait, "duration": LONG_WAIT},
        "M": {"kind": SpawningWaveStepKind.Wait, "duration": MEDIUM_WAIT},
        "S": {"kind": SpawningWaveStepKind.Wait, "duration": SHORT_WAIT},
        "G": {"kind": SpawningWaveStepKind.SpawnEnemy, "enemy_kind": EnemyKind.Grunt},
        "T": {"kind": SpawningWaveStepKind.SpawnEnemy, "enemy_kind": EnemyKind.Tank},
    }

    spawning_waves: list[SpawningWave] = []

    for wave_conf_row in wave_conf.strip().split("\n"):
        wave = [wave_step_map[c] for c in wave_conf_row]
        total_enemy_spawns = sum(
            1 for step in wave if step["kind"] == SpawningWaveStepKind.SpawnEnemy
        )

        # TODO counting total enemy spawns could be in post init of SpawningWave
        spawning_waves.append(
            SpawningWave(wave=wave, total_enemy_spawns=total_enemy_spawns)
        )

    return spawning_waves
