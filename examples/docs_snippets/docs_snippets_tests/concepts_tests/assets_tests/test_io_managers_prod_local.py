import os
from unittest import mock

from docs_snippets.concepts.assets.asset_io_manager_prod_local import defs


@mock.patch.dict(os.environ, {"ENV": "prod"})
def test_prod_assets():
    assert len(defs.get_repository_def().asset_graph.assets_defs) == 2


@mock.patch.dict(os.environ, {"ENV": "local"})
def test_local_assets():
    assert len(defs.get_repository_def().asset_graph.assets_defs) == 2
