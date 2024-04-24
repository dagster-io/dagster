from typing import Any

import mock
import pytest

from dagster._core.definitions.run_config import RunConfig
from dagster._core.errors import DagsterInvalidConfigError


def test_new_resource_testing() -> None:
    from docs_snippets.concepts.resources.pythonic_resources import (
        new_resource_testing,
    )

    new_resource_testing()


def test_new_resource_testing_with_nesting() -> None:
    from docs_snippets.concepts.resources.pythonic_resources import (
        new_resource_testing_with_nesting,
    )

    new_resource_testing_with_nesting()


def test_new_resources_assets_defs() -> None:
    from docs_snippets.concepts.resources.pythonic_resources import (
        new_resources_assets_defs,
    )

    class RequestsResponse:
        def json(self) -> Any:
            return {"foo": "bar"}

    with mock.patch("requests.get", return_value=RequestsResponse()):
        import requests

        defs = new_resources_assets_defs()

        res = defs.get_implicit_global_asset_job_def().execute_in_process()
        assert res.success
        assert res.output_for_node("data_from_url") == {"foo": "bar"}


def test_new_resources_configurable_defs() -> None:
    from docs_snippets.concepts.resources.pythonic_resources import (
        new_resources_configurable_defs,
    )

    class RequestsResponse:
        def json(self) -> Any:
            return {"foo": "bar"}

    with mock.patch("requests.get", return_value=RequestsResponse()):
        import requests

        defs = new_resources_configurable_defs()

        res = defs.get_implicit_global_asset_job_def().execute_in_process()
        assert res.success
        assert res.output_for_node("data_from_service") == {"foo": "bar"}


def test_new_resource_runtime() -> None:
    from docs_snippets.concepts.resources.pythonic_resources import (
        new_resource_runtime,
    )

    defs = new_resource_runtime()

    with pytest.raises(
        DagsterInvalidConfigError,
        match='Missing required config entry "resources" at the root.',
    ):
        res = defs.get_implicit_global_asset_job_def().execute_in_process()

    res = defs.get_implicit_global_asset_job_def().execute_in_process(
        run_config={
            "resources": {
                "db_conn": {
                    "config": {
                        "table": "fake",
                    }
                }
            }
        }
    )
    assert res.success


def test_new_resources_nesting() -> None:
    from docs_snippets.concepts.resources.pythonic_resources import (
        new_resources_nesting,
    )

    defs = new_resources_nesting()
    assert set(defs.get_repository_def().get_top_level_resources().keys()) == {
        "credentials",
        "bucket",
    }
