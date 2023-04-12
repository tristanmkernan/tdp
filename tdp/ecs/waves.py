import random

from .components import SpawningWave
from .enums import EnemyKind, SpawningWaveStepKind
from .types import SpawningWaveStep


# L: long wait
# M: medium wait
# S: short wait
# V: very short wait
# G: grunt
# E: elite
# C: commando
# T: tank
# F: fighter plane
# P: transport plane

SHORT_WAIT = 500.0
VERY_SHORT_WAIT = SHORT_WAIT / 2.0
MEDIUM_WAIT = SHORT_WAIT * 2.5
LONG_WAIT = SHORT_WAIT * 5.0


def generate_random_waves(count=99) -> list[SpawningWave]:
    waves = []
    wave_type_length = 7

    for wave_no in range(count):
        enemies_count = 15 + wave_no

        if wave_no < wave_type_length:
            # training waves
            default_wait = "L"
            enemies = ["G"]
            weights = [1]
        elif wave_no < wave_type_length * 2:
            # ramp up
            default_wait = "M"
            enemies = ["G", "E"]
            weights = [5, 1]
        elif wave_no < wave_type_length * 3:
            default_wait = "M"
            enemies = [
                "G",
                "E",
                "C",
            ]
            weights = [7, 2, 1]
        elif wave_no < wave_type_length * 4:
            default_wait = "M"
            enemies = ["E", "C"]
            weights = [5, 1]
        elif wave_no < wave_type_length * 5:
            default_wait = "M"
            enemies = ["C"]
            weights = [1]
        else:
            default_wait = "S"
            enemies = ["C"]
            weights = [1]

        enemies = random.choices(enemies, weights=weights, k=enemies_count)

        wave_conf = "L" + default_wait.join(enemies) + "LLLLL"

        waves.append(parse_wave(wave_conf))

    return waves


def parse_waves(wave_conf: str) -> list[SpawningWave]:
    spawning_waves: list[SpawningWave] = []

    for wave_conf_row in wave_conf.strip().split("\n"):
        # TODO counting total enemy spawns could be in post init of SpawningWave
        spawning_waves.append(parse_wave(wave_conf_row))

    return spawning_waves


def parse_wave(wave_conf: str) -> SpawningWave:
    wave_step_map: dict[str, SpawningWaveStep] = {
        "L": {"kind": SpawningWaveStepKind.Wait, "duration": LONG_WAIT},
        "M": {"kind": SpawningWaveStepKind.Wait, "duration": MEDIUM_WAIT},
        "S": {"kind": SpawningWaveStepKind.Wait, "duration": SHORT_WAIT},
        "V": {"kind": SpawningWaveStepKind.Wait, "duration": VERY_SHORT_WAIT},
        "G": {"kind": SpawningWaveStepKind.SpawnEnemy, "enemy_kind": EnemyKind.Grunt},
        "T": {"kind": SpawningWaveStepKind.SpawnEnemy, "enemy_kind": EnemyKind.Tank},
        "E": {"kind": SpawningWaveStepKind.SpawnEnemy, "enemy_kind": EnemyKind.Elite},
        "C": {
            "kind": SpawningWaveStepKind.SpawnEnemy,
            "enemy_kind": EnemyKind.Commando,
        },
        "F": {
            "kind": SpawningWaveStepKind.SpawnEnemy,
            "enemy_kind": EnemyKind.FighterPlane,
        },
        "P": {
            "kind": SpawningWaveStepKind.SpawnEnemy,
            "enemy_kind": EnemyKind.TransportPlane,
        },
    }

    wave = [wave_step_map[c] for c in wave_conf]
    total_enemy_spawns = sum(
        1 for step in wave if step["kind"] == SpawningWaveStepKind.SpawnEnemy
    )

    # TODO counting total enemy spawns could be in post init of SpawningWave
    return SpawningWave(wave=wave, total_enemy_spawns=total_enemy_spawns)
