import multiprocessing
import os
import time
from functools import partial
from pathlib import Path
from signal import SIGSEGV

from dagster._utils import run_with_concurrent_update_guard, segfault


def _update_file(file_path: Path):
    time.sleep(0.01)  # fake computation
    file_path.open("a").write(f"write-from-{os.getpid()}\n")


def test_basic(tmp_path: str):
    test_file_path = Path(tmp_path) / "test.txt"

    with multiprocessing.Pool(3) as pool:
        pool.starmap(
            run_with_concurrent_update_guard,
            [(test_file_path, partial(_update_file, test_file_path))] * 3,
        )
    assert test_file_path.read_text()


def test_crashes(tmp_path: str):
    test_file_path = Path(tmp_path) / "test.txt"
    run_guarded = run_with_concurrent_update_guard
    crashing_proc = multiprocessing.Process(
        target=run_guarded,
        args=(test_file_path, segfault),
    )
    crashing_proc.start()
    crashing_proc.join(timeout=1)
    assert crashing_proc.exitcode == -SIGSEGV

    # ensure success can occur with abandoned lock file
    with multiprocessing.Pool(3) as pool:
        pool.starmap(
            run_with_concurrent_update_guard,
            [(test_file_path, partial(_update_file, test_file_path))] * 3,
        )

    assert test_file_path.read_text()


def _maybe(file_path: Path, skip: bool):
    if not skip:
        _update_file(file_path)
    else:
        time.sleep(0.05)


def test_staggered_no_ops(tmp_path: str):
    test_file_path = Path(tmp_path) / "test.txt"
    procs = [
        multiprocessing.Process(
            target=run_with_concurrent_update_guard,
            args=(test_file_path, _maybe),
            kwargs={
                "file_path": test_file_path,
                "skip": i % 2 == 0,
            },
        )
        for i in range(6)
    ]

    for proc in procs:
        proc.start()
        time.sleep(0.025)

    for proc in procs:
        proc.join(timeout=1)
        assert proc.exitcode == 0

    assert test_file_path.read_text()
