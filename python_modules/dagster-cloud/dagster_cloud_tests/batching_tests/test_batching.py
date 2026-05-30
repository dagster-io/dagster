import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from dagster_cloud.batching.batcher import (
    DEFAULT_MAX_BATCH_SIZE,
    DEFAULT_MAX_QUEUE_SIZE,
    DEFAULT_MAX_WAIT_MS,
    Batcher,
)


class BatchingTestCase(unittest.TestCase):
    def test_batching(self):
        batches = _test(list(range(10)))
        assert sum(len(b) for b in batches) == 10

    def test_batching_maxsize(self):
        batches = _test(list(range(20)), max_batch_size=5)
        for batch in batches:
            assert len(batch) <= 5

    def test_batch_failure(self):
        def handler(batch: list[int]) -> list[int]:
            raise Exception("failing")

        batcher = Batcher("test", handler)

        def _do_submit(i: int) -> None:
            with self.assertRaises(Exception, msg="failing"):
                batcher.submit(i)

        with ThreadPoolExecutor() as executor:
            list(executor.map(_do_submit, list(range(10))))

    def test_config(self):
        def handler(f: list[int]) -> list[int]:
            return f

        batcher: Batcher[int, int] = Batcher(
            "test",
            handler,
        )
        assert batcher._max_wait_ms == DEFAULT_MAX_WAIT_MS  # noqa: SLF001
        assert batcher._max_batch_size == DEFAULT_MAX_BATCH_SIZE  # noqa: SLF001
        assert batcher._queue.maxsize == DEFAULT_MAX_QUEUE_SIZE  # noqa: SLF001

        batcher: Batcher[int, int] = Batcher(
            "test",
            handler,
            max_wait_ms=10,
            max_batch_size=11,
            max_queue_size=12,
        )
        assert batcher._max_wait_ms == 10  # noqa: SLF001
        assert batcher._max_batch_size == 11  # noqa: SLF001
        assert batcher._queue.maxsize == 12  # noqa: SLF001

        with patch.dict(
            "os.environ",
            {
                "DAGSTER_BATCHING__TEST__MAX_WAIT_MS": "100",
                "DAGSTER_BATCHING__TEST__MAX_BATCH_SIZE": "101",
                "DAGSTER_BATCHING__TEST__MAX_QUEUE_SIZE": "102",
            },
        ):
            batcher: Batcher[int, int] = Batcher(
                "test",
                handler,
                max_wait_ms=10,
                max_batch_size=11,
                max_queue_size=12,
            )
            assert batcher._max_wait_ms == 100  # noqa: SLF001
            assert batcher._max_batch_size == 101  # noqa: SLF001
            assert batcher._queue.maxsize == 102  # noqa: SLF001


def _test(items: list[int], max_batch_size: int | None = None) -> list[list[int]]:
    batches = []

    def handler(batch: list[int]) -> list[int]:
        batches.append(batch)
        return [x + 1 for x in batch]

    batcher = Batcher("test", handler, max_batch_size=max_batch_size)

    def run():
        def _do_submit(i: int) -> None:
            assert batcher.submit(i) == i + 1

        with ThreadPoolExecutor() as executor:
            list(executor.map(_do_submit, items))

    run()
    return batches
