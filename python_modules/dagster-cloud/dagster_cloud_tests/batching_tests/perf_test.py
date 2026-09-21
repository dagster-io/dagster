"""(very) small perf testing script for batcher that spins up
a large number of threads and tries to detect overhead of lock
contention in the batcher. the handler sleeps for 100ms
imitating a db call, and so you should be able to compute what
the expected runtime should be (for example, with n=10k,
max_workers=100, max_batch_size=100, it should take 100 * 100ms = 10s
(the batcher coalesces work across threads)).
"""

import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import structlog
from dagster_cloud.batching.batcher import Batcher
from typer import Typer

logger = structlog.get_logger(__name__)

app = Typer()


def load_test(n: int, max_batch_size: int):
    def handler(xs: list[int]) -> list[int]:
        time.sleep(0.1)
        return [x + 1 for x in xs]

    batcher: Batcher[int, int] = Batcher(
        "test",
        handler,
        max_batch_size=max_batch_size,
    )

    with ThreadPoolExecutor(max_workers=100) as pool:
        result = list(pool.map(batcher.submit, range(n)))

    assert result == list(range(1, n + 1))


@contextmanager
def timeit(n: int):
    s = time.monotonic()
    yield
    e = time.monotonic()
    logger.info(f"took {e - s} seconds for {n} iterations")


@app.command()
def command(n: int, max_batch_size: int = 100):
    with timeit(n):
        load_test(n, max_batch_size)


if __name__ == "__main__":
    app()
