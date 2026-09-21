from dagster._daemon.utils import shuffled_round_robin_by_key


def test_shuffled_round_robin_by_key_empty():
    assert shuffled_round_robin_by_key([], key=str) == []


def test_shuffled_round_robin_by_key_single_group():
    items = [("a", 1), ("a", 2), ("a", 3)]
    result = shuffled_round_robin_by_key(items, key=lambda x: x[0])
    assert sorted(result) == sorted(items)
    assert all(x[0] == "a" for x in result)


def test_shuffled_round_robin_by_key_preserves_membership():
    items = (
        [("a", i) for i in range(5)] + [("b", i) for i in range(2)] + [("c", i) for i in range(3)]
    )
    result = shuffled_round_robin_by_key(items, key=lambda x: x[0])
    assert sorted(result) == sorted(items)


def test_shuffled_round_robin_by_key_round_robin_pattern():
    # First N items must hit each group at least once, where N = number of groups.
    # This invariant is guaranteed by round-robin regardless of how the shuffles fall.
    items = (
        [("a", i) for i in range(10)]
        + [("b", i) for i in range(10)]
        + [("c", i) for i in range(10)]
    )
    result = shuffled_round_robin_by_key(items, key=lambda x: x[0])
    first_three_groups = {x[0] for x in result[:3]}
    assert first_three_groups == {"a", "b", "c"}


def test_shuffled_round_robin_by_key_heavy_group_does_not_starve_light():
    # Sparse-group fairness: a single item in its own group must land in the first
    # `num_groups` positions, no matter how heavy the other groups are. With two
    # groups the light item lands at position 0 or 1 by the round-robin invariant.
    items = [("heavy", i) for i in range(100)] + [("light", 0)]
    result = shuffled_round_robin_by_key(items, key=lambda x: x[0])
    light_pos = result.index(("light", 0))
    assert light_pos < 2, (
        f"light item should land in the first 2 positions (one per group), got {light_pos}"
    )
