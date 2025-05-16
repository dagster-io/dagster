import shutil
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

import pytest
import yaml
from click.testing import CliRunner
from dagster import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetMaterialization
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.instance_for_test import instance_for_test
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster._utils import alter_sys_path
from dagster._utils.env import environ
from dagster.components import ComponentLoadContext
from dagster.components.cli import cli
from dagster.components.resolved.context import ResolutionException
from dagster.components.resolved.core_models import AssetAttributesModel
from dagster_sling import SlingReplicationCollectionComponent, SlingResource

ensure_dagster_tests_import()

from dagster_tests.components_tests.utils import (
    build_component_defs_for_test,
    get_underlying_component,
    temp_code_location_bar,
)

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition

STUB_LOCATION_PATH = Path(__file__).parent / "code_locations" / "sling_location"
COMPONENT_RELPATH = "defs/ingest"
REPLICATION_PATH = STUB_LOCATION_PATH / COMPONENT_RELPATH / "replication.yaml"


@contextmanager
def _modify_yaml(path: Path) -> Iterator[dict[str, Any]]:
    with open(path) as f:
        data = yaml.safe_load(f)
    yield data  # modify data here
    with open(path, "w") as f:
        yaml.dump(data, f)


@contextmanager
def temp_sling_component_instance(
    replication_specs: Optional[list[dict[str, Any]]] = None,
) -> Iterator[tuple[SlingReplicationCollectionComponent, Definitions]]:
    """Sets up a temporary directory with a replication.yaml and defs.yaml file that reference
    the proper temp path.
    """
    with (
        tempfile.TemporaryDirectory() as temp_dir,
        alter_sys_path(to_add=[str(temp_dir)], to_remove=[]),
    ):
        with environ({"HOME": temp_dir, "SOME_PASSWORD": "password"}):
            shutil.copytree(STUB_LOCATION_PATH, temp_dir, dirs_exist_ok=True)
            component_path = Path(temp_dir) / COMPONENT_RELPATH

            # update the replication yaml to reference a CSV file in the tempdir
            with _modify_yaml(component_path / "replication.yaml") as data:
                placeholder_data = data["streams"].pop("<PLACEHOLDER>")
                data["streams"][f"file://{temp_dir}/input.csv"] = placeholder_data

            with _modify_yaml(component_path / "defs.yaml") as data:
                # If replication specs were provided, overwrite the default one in the defs.yaml
                if replication_specs:
                    data["attributes"]["replications"] = replication_specs

                # update the defs yaml to add a duckdb instance
                data["attributes"]["sling"]["connections"][0]["instance"] = f"{temp_dir}/duckdb"

            context = ComponentLoadContext.for_test().for_path(component_path)
            component = get_underlying_component(context)
            assert isinstance(component, SlingReplicationCollectionComponent)
            yield component, component.build_defs(context)


def test_python_attributes() -> None:
    with temp_sling_component_instance([{"path": "./replication.yaml"}]) as (component, defs):
        replications = component.replications
        assert len(replications) == 1
        op = replications[0].op
        assert op is None

        assert defs.get_asset_graph().get_all_asset_keys() == {
            AssetKey("input_csv"),
            AssetKey("input_duckdb"),
        }
        # inherited from directory name
        assert defs.get_assets_def("input_duckdb").op.name == "replication"


def test_python_attributes_op_name() -> None:
    with temp_sling_component_instance(
        [{"path": "./replication.yaml", "op": {"name": "my_op"}}]
    ) as (component, defs):
        replications = component.replications
        assert len(replications) == 1
        op = replications[0].op
        assert op
        assert op.name == "my_op"
        assert defs.get_asset_graph().get_all_asset_keys() == {
            AssetKey("input_csv"),
            AssetKey("input_duckdb"),
        }
        assert defs.get_assets_def("input_duckdb").op.name == "my_op"


def test_python_attributes_op_tags() -> None:
    with temp_sling_component_instance(
        [{"path": "./replication.yaml", "op": {"tags": {"tag1": "value1"}}}]
    ) as (component, defs):
        replications = component.replications
        assert len(replications) == 1
        op = replications[0].op
        assert op
        assert op.tags == {"tag1": "value1"}
        assert defs.get_assets_def("input_duckdb").op.tags == {"tag1": "value1"}


def test_python_params_include_metadata() -> None:
    with temp_sling_component_instance(
        [{"path": "./replication.yaml", "include_metadata": ["column_metadata", "row_count"]}]
    ) as (component, defs):
        replications = component.replications
        assert len(replications) == 1
        include_metadata = replications[0].include_metadata
        assert include_metadata == ["column_metadata", "row_count"]

        input_duckdb = defs.get_assets_def("input_duckdb")

        with instance_for_test() as instance:
            result = materialize([input_duckdb], instance=instance)
        materializations = result.get_asset_materialization_events()
        assert len(materializations) == 1
        materialization = materializations[0].materialization
        assert "dagster/row_count" in materialization.metadata
        assert "dagster/column_schema" in materialization.metadata


def test_load_from_path() -> None:
    with temp_sling_component_instance() as (component, defs):
        resource = getattr(component, "resource")
        assert isinstance(resource, SlingResource)
        assert len(resource.connections) == 1
        assert resource.connections[0].name == "DUCKDB"
        assert resource.connections[0].type == "duckdb"
        assert resource.connections[0].password == "password"

        assert defs.get_asset_graph().get_all_asset_keys() == {
            AssetKey("input_csv"),
            AssetKey(["foo", "input_duckdb"]),
        }


def test_sling_subclass() -> None:
    class DebugSlingReplicationComponent(SlingReplicationCollectionComponent):
        def execute(  # pyright: ignore[reportIncompatibleMethodOverride]
            self, context: AssetExecutionContext, sling: SlingResource
        ) -> Iterator[Union[AssetMaterialization, MaterializeResult]]:
            return sling.replicate(context=context, debug=True)

    defs = build_component_defs_for_test(
        DebugSlingReplicationComponent,
        {"sling": {}, "replications": [{"path": str(REPLICATION_PATH)}]},
    )
    assert defs.get_asset_graph().get_all_asset_keys() == {
        AssetKey("input_csv"),
        AssetKey("input_duckdb"),
    }


@pytest.mark.parametrize(
    "attributes, assertion, should_error",
    [
        ({"group_name": "group"}, lambda asset_spec: asset_spec.group_name == "group", False),
        (
            {"owners": ["team:analytics"]},
            lambda asset_spec: asset_spec.owners == ["team:analytics"],
            False,
        ),
        ({"tags": {"foo": "bar"}}, lambda asset_spec: asset_spec.tags.get("foo") == "bar", False),
        ({"kinds": ["snowflake"]}, lambda asset_spec: "snowflake" in asset_spec.kinds, False),
        (
            {"tags": {"foo": "bar"}, "kinds": ["snowflake"]},
            lambda asset_spec: "snowflake" in asset_spec.kinds
            and asset_spec.tags.get("foo") == "bar",
            False,
        ),
        ({"code_version": "1"}, lambda asset_spec: asset_spec.code_version == "1", False),
        (
            {"description": "some description"},
            lambda asset_spec: asset_spec.description == "some description",
            False,
        ),
        (
            {"metadata": {"foo": "bar"}},
            lambda asset_spec: asset_spec.metadata.get("foo") == "bar",
            False,
        ),
        (
            {"deps": ["customers"]},
            lambda asset_spec: {dep.asset_key for dep in asset_spec.deps}
            == {AssetKey("customers")},
            False,
        ),
        (
            {"automation_condition": "{{ automation_condition.eager() }}"},
            lambda asset_spec: asset_spec.automation_condition is not None,
            False,
        ),
        (
            {"key": "overridden_key"},
            lambda asset_spec: asset_spec.key == AssetKey("overridden_key"),
            False,
        ),
        (
            {"key_prefix": "overridden_prefix"},
            lambda asset_spec: asset_spec.key.has_prefix(["overridden_prefix"]),
            False,
        ),
    ],
    ids=[
        "group_name",
        "owners",
        "tags",
        "kinds",
        "tags-and-kinds",
        "code-version",
        "description",
        "metadata",
        "deps",
        "automation_condition",
        "key",
        "key_prefix",
    ],
)
def test_translation(
    attributes: Mapping[str, Any],
    assertion: Optional[Callable[[AssetSpec], bool]],
    should_error: bool,
) -> None:
    wrapper = pytest.raises(ResolutionException) if should_error else nullcontext()
    with (
        wrapper,
        temp_sling_component_instance(
            [{"path": "./replication.yaml", "translation": attributes}]
        ) as (component, defs),
    ):
        key = AssetKey(attributes.get("key", "input_duckdb"))
        if attributes.get("key_prefix"):
            key = key.with_prefix(attributes["key_prefix"])

        assets_def: AssetsDefinition = defs.get_assets_def(key)
    if assertion:
        assert assertion(assets_def.get_asset_spec(key))


IGNORED_KEYS = {"skippable"}


def test_translation_is_comprehensive():
    all_asset_attribute_keys = []
    for test_arg in test_translation.pytestmark[0].args[1]:  # pyright: ignore[reportFunctionMemberAccess]
        all_asset_attribute_keys.extend(test_arg[0].keys())
    from dagster.components.resolved.core_models import AssetAttributesModel

    assert set(AssetAttributesModel.model_fields.keys()) - IGNORED_KEYS == set(
        all_asset_attribute_keys
    ), (
        f"The test_translation test does not cover all fields, missing: {set(AssetAttributesModel.model_fields.keys()) - IGNORED_KEYS - set(all_asset_attribute_keys)}"
    )


def test_scaffold_sling():
    runner = CliRunner()

    with temp_code_location_bar():
        result = runner.invoke(
            cli,
            [
                "scaffold",
                "object",
                "dagster_sling.SlingReplicationCollectionComponent",
                "bar/components/qux",
                "--scaffold-format",
                "yaml",
            ],
        )
        assert result.exit_code == 0
        assert Path("bar/components/qux/replication.yaml").exists()
        assert Path("bar/components/qux/defs.yaml").exists()


def test_spec_is_available_in_scope() -> None:
    with temp_sling_component_instance(
        [
            {
                "path": "./replication.yaml",
                "translation": {"metadata": {"asset_key": "{{ spec.key.path }}"}},
            }
        ]
    ) as (_, defs):
        assets_def: AssetsDefinition = defs.get_assets_def("input_duckdb")
        assert assets_def.get_asset_spec(AssetKey("input_duckdb")).metadata["asset_key"] == [
            "input_duckdb"
        ]


def map_spec(spec: AssetSpec) -> AssetSpec:
    return spec.replace_attributes(tags={"is_custom_spec": "yes"})


def map_spec_to_attributes(spec: AssetSpec):
    return AssetAttributesModel(tags={"is_custom_spec": "yes"})


def map_spec_to_attributes_dict(spec: AssetSpec) -> dict[str, Any]:
    return {"tags": {"is_custom_spec": "yes"}}


@pytest.mark.parametrize("map_fn", [map_spec, map_spec_to_attributes, map_spec_to_attributes_dict])
def test_udf_map_spec(map_fn: Callable[[AssetSpec], Any]) -> None:
    class DebugSlingReplicationComponent(SlingReplicationCollectionComponent):
        @classmethod
        def get_additional_scope(cls) -> Mapping[str, Any]:
            return {"map_spec": map_fn}

    defs = build_component_defs_for_test(
        DebugSlingReplicationComponent,
        {
            "sling": {},
            "replications": [
                {"path": str(REPLICATION_PATH), "translation": "{{ map_spec(spec) }}"}
            ],
        },
    )

    assets_def: AssetsDefinition = defs.get_assets_def(AssetKey("input_duckdb"))
    assert assets_def.get_asset_spec(AssetKey("input_duckdb")).tags["is_custom_spec"] == "yes"
