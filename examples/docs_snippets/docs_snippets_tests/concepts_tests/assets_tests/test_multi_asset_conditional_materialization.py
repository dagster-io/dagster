from unittest.mock import patch

from dagster import materialize_to_memory
from docs_snippets.concepts.assets.multi_asset_conditional_materialization import (
    assets_1_and_2,
    downstream1,
    downstream2,
)


def test_multi_asset_conditional_materialization():
    with patch("random.randint") as r:
        r.side_effect = [4, 6]
        result1 = materialize_to_memory([assets_1_and_2, downstream1, downstream2])
        assert len(result1.asset_materializations_for_node("assets_1_and_2")) == 1
        assert len(result1.asset_materializations_for_node("downstream1")) == 1
        assert len(result1.asset_materializations_for_node("downstream2")) == 0
        assert len(result1.get_step_skipped_events()) == 1

        r.side_effect = [6, 4]
        result2 = materialize_to_memory([assets_1_and_2, downstream1, downstream2])
        assert len(result2.asset_materializations_for_node("assets_1_and_2")) == 1
        assert len(result2.asset_materializations_for_node("downstream1")) == 0
        assert len(result2.asset_materializations_for_node("downstream2")) == 1
        assert len(result2.get_step_skipped_events()) == 1
