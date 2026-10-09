from dagster_graphql.implementation.utils import get_query_limit_with_default

# ##### TESTS


def test_get_query_limit_with_default_clamps():
    # no limit provided falls back to the default
    assert get_query_limit_with_default(None, 1000) == 1000

    # under and at the default are returned unchanged
    assert get_query_limit_with_default(1, 1000) == 1
    assert get_query_limit_with_default(999, 1000) == 999
    assert get_query_limit_with_default(1000, 1000) == 1000

    # over the default clamps instead of raising
    assert get_query_limit_with_default(1001, 1000) == 1000
    assert get_query_limit_with_default(5000, 1000) == 1000
    assert get_query_limit_with_default(1000, 500) == 500
