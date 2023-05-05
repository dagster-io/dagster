from unittest.mock import patch

from dagster import materialize_to_memory
from docs_snippets.concepts.assets.conditional_materialization import (
    downstream,
    may_not_materialize,
)


def test_conditional_materialization():
    with patch("random.randint") as r:
        r.return_value = 4
        result1 = materialize_to_memory([downstream, may_not_materialize])
        assert len(result1.asset_materializations_for_node("may_not_materialize")) == 1
        assert len(result1.asset_materializations_for_node("downstream")) == 1
        assert len(result1.get_step_skipped_events()) == 0

        r.return_value = 6
        result2 = materialize_to_memory([downstream, may_not_materialize])
        assert len(result2.asset_materializations_for_node("may_not_materialize")) == 0
        assert len(result2.asset_materializations_for_node("downstream")) == 0
        assert len(result2.get_step_skipped_events()) == 1
