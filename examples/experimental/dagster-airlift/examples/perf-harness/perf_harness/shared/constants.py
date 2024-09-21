from pathlib import Path
from typing import Dict

CONSTANTS_FILE = Path(__file__).parent / "constants.txt"


def read_constants() -> Dict[str, int]:
    constants = {}
    with open(CONSTANTS_FILE, "r") as f:
        for line in f.readlines():
            key, value = line.strip().split(None, 1)
            constants[key] = int(value)
    return constants


def get_num_dags() -> int:
    constants = read_constants()
    if "NUM_DAGS" not in constants:
        raise ValueError("NUM_DAGS not found in constants file")
    return constants["NUM_DAGS"]


def get_num_tasks() -> int:
    constants = read_constants()
    if "NUM_TASKS" not in constants:
        raise ValueError("NUM_TASKS not found in constants file")
    return constants["NUM_TASKS"]


def get_num_assets() -> int:
    constants = read_constants()
    if "NUM_ASSETS_PER_TASK" not in constants:
        raise ValueError("NUM_ASSETS_PER_TASK not found in constants file")
    return constants["NUM_ASSETS_PER_TASK"]


def get_perf_output_file() -> Path:
    pth = Path(__file__).parent / f"{get_num_dags()}_dags_{get_num_tasks()}_tasks_perf_output.txt"
    pth.parent.mkdir(parents=True, exist_ok=True)
    return pth
