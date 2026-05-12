from collections import Counter

from dagster._core.storage.cached_has_table_method import cached_has_table_method


class MyStorage:
    def __init__(self, tables: set[str] | None = None) -> None:
        self._tables: set[str] = tables if tables is not None else {"t1"}
        self.call_counts: Counter[str] = Counter()

    @cached_has_table_method
    def has_table(self, table_name: str) -> bool:
        self.call_counts[table_name] += 1
        return table_name in self._tables

    def create_table(self, table_name: str) -> None:
        self._tables.add(table_name)


def test_cached_has_table_method_caches_true() -> None:
    storage = MyStorage()
    assert storage.has_table("t1") is True
    assert storage.call_counts.total() == storage.call_counts["t1"] == 1

    assert storage.has_table("t1") is True
    assert storage.call_counts.total() == storage.call_counts["t1"] == 1


def test_cached_has_table_method_does_not_cache_false() -> None:
    storage = MyStorage()
    assert storage.has_table("missing") is False
    assert storage.call_counts.total() == storage.call_counts["missing"] == 1

    assert storage.has_table("missing") is False
    assert storage.call_counts.total() == storage.call_counts["missing"] == 2


def test_cached_has_table_method_caches_after_table_created() -> None:
    """False is not cached; once a table exists (True) the result is cached."""
    storage = MyStorage()
    assert storage.has_table("t2") is False  # call 1
    assert storage.call_counts.total() == storage.call_counts["t2"] == 1

    storage.create_table("t2")
    assert storage.has_table("t2") is True  # call 2: now True, cached
    assert storage.call_counts.total() == storage.call_counts["t2"] == 2

    assert storage.has_table("t2") is True  # cached, not re-computed
    assert storage.call_counts.total() == storage.call_counts["t2"] == 2


def test_cached_has_table_method_per_table_isolation() -> None:
    storage = MyStorage()
    assert storage.has_table("t1") is True
    assert storage.call_counts.total() == storage.call_counts["t1"] == 1
    assert storage.call_counts["t2"] == 0

    assert storage.has_table("t2") is False
    assert storage.call_counts.total() == 2
    assert storage.call_counts["t1"] == storage.call_counts["t2"] == 1

    assert storage.has_table("t1") is True  # cached
    assert storage.call_counts.total() == 2
    assert storage.call_counts["t1"] == storage.call_counts["t2"] == 1

    assert storage.has_table("t2") is False  # not cached
    assert storage.call_counts.total() == 3
    assert storage.call_counts["t1"] == 1
    assert storage.call_counts["t2"] == 2


def test_cached_has_table_method_per_instance_isolation() -> None:
    s1 = MyStorage({"t1"})
    s2 = MyStorage(set())

    assert s1.has_table("t1") is True
    assert s1.call_counts.total() == s1.call_counts["t1"] == 1
    assert s2.call_counts.total() == s2.call_counts["t1"] == 0

    assert s2.has_table("t1") is False
    assert s1.call_counts.total() == s1.call_counts["t1"] == 1
    assert s2.call_counts.total() == s2.call_counts["t1"] == 1

    assert s1.has_table("t1") is True  # cached on s1
    assert s1.call_counts.total() == s1.call_counts["t1"] == 1
    assert s2.call_counts.total() == s2.call_counts["t1"] == 1

    assert s2.has_table("t1") is False  # not cached on s2
    assert s1.call_counts.total() == s1.call_counts["t1"] == 1
    assert s2.call_counts.total() == s2.call_counts["t1"] == 2
