import logging
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from types import ModuleType
from typing import Any, cast
from unittest.mock import MagicMock, patch

import dagster as dg
import pytest
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.module_loaders.load_assets_from_modules import (
    load_assets_from_modules,
)
from dagster._core.definitions.module_loaders.load_defs_from_module import (
    load_definitions_from_current_module,
    load_definitions_from_module,
    load_definitions_from_modules,
    load_definitions_from_package_module,
    load_definitions_from_package_name,
)
from dagster._core.definitions.module_loaders.object_list import (
    LoadableDagsterDef,
    ModuleScopedDagsterDefs,
)
from dagster._record import record


def build_module_fake(name: str, objects: Mapping[str, Any]) -> ModuleType:
    module = ModuleType(name)
    for key, value in objects.items():
        setattr(module, key, value)
    return module


def asset_with_key(key: str) -> dg.AssetsDefinition:
    @dg.asset(key=key)
    def my_asset(): ...

    return my_asset


def schedule_with_name(name: str) -> dg.ScheduleDefinition:
    return dg.ScheduleDefinition(name=name, cron_schedule="* * * * *", target="*")


def sensor_with_name(name: str) -> dg.SensorDefinition:
    @dg.sensor(job_name="blah")
    def my_sensor():
        pass

    return my_sensor


def check_with_key(key: str, name: str) -> dg.AssetChecksDefinition:
    @dg.asset_check(asset=key, name=name)
    def my_check() -> dg.AssetCheckResult:
        raise Exception("ooops")

    return my_check


def all_loadable_objects_from_defs(defs: Definitions) -> Sequence[LoadableDagsterDef]:
    return [
        *(defs.assets or []),
        *(defs.sensors or []),
        *(defs.schedules or []),
        *(defs.asset_checks or []),
        *(defs.jobs or []),
    ]


@contextmanager
def optional_pytest_raise(error_expected: bool, exception_cls: type[Exception]):
    if error_expected:
        with pytest.raises(exception_cls):
            yield
    else:
        yield


@record
class ModuleScopeTestSpec:
    objects: Mapping[str, Any]
    error_expected: bool
    id_: str

    @staticmethod
    def as_parametrize_kwargs(seq: Sequence["ModuleScopeTestSpec"]) -> Mapping[str, Any]:
        return {
            "argnames": "objects,error_expected",
            "argvalues": [(spec.objects, spec.error_expected) for spec in seq],
            "ids": [spec.id_ for spec in seq],
        }


some_schedule = schedule_with_name("foo")
some_sensor = sensor_with_name("foo")
some_asset = asset_with_key("foo")
some_job = dg.define_asset_job(name="foo")
some_check = check_with_key("foo_key", "some_name")
partitioned_job = dg.define_asset_job(
    name="foo", partitions_def=dg.DailyPartitionsDefinition(start_date="2020-01-01")
)
some_partitioned_schedule = dg.build_schedule_from_partitioned_job(partitioned_job, "0 0 * * *")
other_partitioned_schedule = dg.build_schedule_from_partitioned_job(partitioned_job, "0 0 * * *")


MODULE_TEST_SPECS = [
    ModuleScopeTestSpec(
        objects={"foo": some_schedule}, error_expected=False, id_="single schedule"
    ),
    ModuleScopeTestSpec(
        objects={"foo": some_schedule, "bar": schedule_with_name("foo")},
        error_expected=True,
        id_="conflicting schedules",
    ),
    ModuleScopeTestSpec(
        objects={"foo": some_schedule, "bar": some_schedule},
        error_expected=False,
        id_="schedules multiple variables",
    ),
    ModuleScopeTestSpec(objects={"foo": some_sensor}, error_expected=False, id_="single sensor"),
    ModuleScopeTestSpec(
        objects={"foo": some_sensor, "bar": sensor_with_name("foo")},
        error_expected=True,
        id_="conflicting sensors",
    ),
    ModuleScopeTestSpec(
        objects={"foo": some_sensor, "bar": some_sensor},
        error_expected=False,
        id_="sensors multiple variables",
    ),
    ModuleScopeTestSpec(
        objects={"foo": some_asset},
        error_expected=False,
        id_="asset single variable",
    ),
    ModuleScopeTestSpec(
        objects={"foo": some_asset, "bar": asset_with_key("foo")},
        error_expected=True,
        id_="conflicting assets",
    ),
    ModuleScopeTestSpec(
        objects={"foo": some_asset, "bar": some_asset},
        error_expected=False,
        id_="assets multiple variables",
    ),
    ModuleScopeTestSpec(
        objects={"foo": some_job},
        error_expected=False,
        id_="single job",
    ),
    ModuleScopeTestSpec(
        objects={"foo": some_job, "bar": dg.define_asset_job("other_job")},
        error_expected=False,
        id_="conflicting jobs",
    ),
    ModuleScopeTestSpec(
        objects={"foo": some_job, "bar": some_job},
        error_expected=False,
        id_="job multiple variables",
    ),
    ModuleScopeTestSpec(
        objects={"foo": some_check},
        error_expected=False,
        id_="single job",
    ),
    # Currently, we do not perform any collision detection on asset checks. This is the behavior currently public in load_asset_checks_from_module.
    ModuleScopeTestSpec(
        objects={"foo": some_check, "bar": check_with_key("foo_key", "some_name")},
        error_expected=False,
        id_="conflicting checks",
    ),
    ModuleScopeTestSpec(
        objects={"foo": some_check, "bar": some_check},
        error_expected=False,
        id_="check multiple variables",
    ),
    ModuleScopeTestSpec(
        objects={"foo": some_partitioned_schedule, "job": partitioned_job},
        error_expected=False,
        id_="single partitioned schedule",
    ),
    ModuleScopeTestSpec(
        objects={
            "foo": some_partitioned_schedule,
            "bar": other_partitioned_schedule,
            "job": partitioned_job,
        },
        error_expected=True,
        id_="conflicting partitioned schedules",
    ),
    ModuleScopeTestSpec(
        objects={
            "foo": some_partitioned_schedule,
            "bar": some_partitioned_schedule,
            "job": partitioned_job,
        },
        error_expected=False,
        id_="partitioned schedules multiple variables",
    ),
]


@pytest.mark.parametrize(**ModuleScopeTestSpec.as_parametrize_kwargs(MODULE_TEST_SPECS))
def test_collision_detection(objects: Mapping[str, Any], error_expected: bool) -> None:
    module_fake = build_module_fake("fake", objects)
    with optional_pytest_raise(
        error_expected=error_expected, exception_cls=dg.DagsterInvalidDefinitionError
    ):
        obj_list = ModuleScopedDagsterDefs.from_modules([module_fake]).get_object_list()
        obj_ids = {id(obj) for obj in objects.values()}
        assert len(obj_list.loaded_defs) == len(obj_ids)


@pytest.mark.parametrize(**ModuleScopeTestSpec.as_parametrize_kwargs(MODULE_TEST_SPECS))
def test_load_from_definitions_from_modules(
    objects: Mapping[str, Any], error_expected: bool
) -> None:
    module_fake = build_module_fake("fake", objects)
    with optional_pytest_raise(
        error_expected=error_expected, exception_cls=dg.DagsterInvalidDefinitionError
    ):
        defs = load_definitions_from_modules([module_fake])
        obj_ids = {id(obj) for obj in all_loadable_objects_from_defs(defs)}
        expected_obj_ids = {id(obj) for obj in objects.values()}
        assert len(obj_ids) == len(expected_obj_ids)


@pytest.mark.parametrize(**ModuleScopeTestSpec.as_parametrize_kwargs(MODULE_TEST_SPECS))
def test_load_from_definitions_from_module(
    objects: Mapping[str, Any], error_expected: bool
) -> None:
    module_fake = build_module_fake("fake", objects)
    with optional_pytest_raise(
        error_expected=error_expected, exception_cls=dg.DagsterInvalidDefinitionError
    ):
        defs = load_definitions_from_module(module_fake)
        obj_ids = {id(obj) for obj in all_loadable_objects_from_defs(defs)}
        expected_obj_ids = {id(obj) for obj in objects.values()}
        assert len(obj_ids) == len(expected_obj_ids)


@pytest.mark.parametrize(**ModuleScopeTestSpec.as_parametrize_kwargs(MODULE_TEST_SPECS))
@patch("dagster._core.definitions.module_loaders.load_defs_from_module.inspect.getmodule")
def test_load_from_definitions_from_current_module(
    mock_getmodule: MagicMock, objects: Mapping[str, Any], error_expected: bool
) -> None:
    module_fake = build_module_fake("fake", objects)
    mock_getmodule.return_value = module_fake

    with optional_pytest_raise(
        error_expected=error_expected, exception_cls=dg.DagsterInvalidDefinitionError
    ):
        defs = load_definitions_from_current_module()
        obj_ids = {id(obj) for obj in all_loadable_objects_from_defs(defs)}
        expected_obj_ids = {id(obj) for obj in objects.values()}
        assert len(obj_ids) == len(expected_obj_ids)


@pytest.mark.parametrize(**ModuleScopeTestSpec.as_parametrize_kwargs(MODULE_TEST_SPECS))
@patch("dagster._core.definitions.module_loaders.load_defs_from_module.find_modules_in_package")
def test_load_from_definitions_from_package_module(
    mock_module_finder: MagicMock, objects: Mapping[str, Any], error_expected: bool
) -> None:
    package_fake = build_module_fake("fake_package", {})
    module_fake = build_module_fake("fake", objects)

    mock_module_finder.return_value = [module_fake]
    with optional_pytest_raise(
        error_expected=error_expected, exception_cls=dg.DagsterInvalidDefinitionError
    ):
        defs = load_definitions_from_package_module(package_fake)
        obj_ids = {id(obj) for obj in all_loadable_objects_from_defs(defs)}
        expected_obj_ids = {id(obj) for obj in objects.values()}
        assert len(obj_ids) == len(expected_obj_ids)


@pytest.mark.parametrize(**ModuleScopeTestSpec.as_parametrize_kwargs(MODULE_TEST_SPECS))
@patch("dagster._core.definitions.module_loaders.load_defs_from_module.find_modules_in_package")
@patch("dagster._core.definitions.module_loaders.load_defs_from_module.import_module")
def test_load_from_definitions_from_package_name(
    mock_module_importer: MagicMock,
    mock_module_finder: MagicMock,
    objects: Mapping[str, Any],
    error_expected: bool,
) -> None:
    package_name_fake = "fake_package"
    package_fake = build_module_fake(package_name_fake, {})
    module_fake = build_module_fake("fake", objects)

    mock_module_importer.return_value = package_fake
    mock_module_finder.return_value = [module_fake]
    with optional_pytest_raise(
        error_expected=error_expected, exception_cls=dg.DagsterInvalidDefinitionError
    ):
        defs = load_definitions_from_package_name(package_name_fake)
        obj_ids = {id(obj) for obj in all_loadable_objects_from_defs(defs)}
        expected_obj_ids = {id(obj) for obj in objects.values()}
        assert len(obj_ids) == len(expected_obj_ids)


def test_load_with_resources() -> None:
    @dg.resource
    def my_resource(): ...

    module_fake = build_module_fake("foo", {"my_resource": my_resource})
    defs = load_definitions_from_module(module_fake)
    assert len(all_loadable_objects_from_defs(defs)) == 0
    assert len(defs.resources or {}) == 0
    defs = load_definitions_from_module(module_fake, resources={"foo": my_resource})
    assert len(defs.resources or {}) == 1


def test_load_with_logger_defs() -> None:
    @dg.logger(config_schema={})
    def my_logger(init_context) -> logging.Logger: ...

    module_fake = build_module_fake("foo", {"my_logger": my_logger})
    defs = load_definitions_from_module(module_fake)
    assert len(all_loadable_objects_from_defs(defs)) == 0
    assert len(defs.resources or {}) == 0
    defs = load_definitions_from_module(module_fake, resources={"foo": my_logger})
    assert len(defs.resources or {}) == 1


def test_load_with_executor() -> None:
    @dg.executor(name="my_executor")
    def my_executor(init_context) -> dg.Executor: ...

    module_fake = build_module_fake("foo", {"my_executor": my_executor})
    defs = load_definitions_from_module(module_fake)
    assert len(all_loadable_objects_from_defs(defs)) == 0
    assert defs.executor is None
    defs = load_definitions_from_module(module_fake, executor=my_executor)
    assert (
        defs.executor is not None
        and cast(dg.ExecutorDefinition, defs.executor).name == "my_executor"
    )


def test_asset_loader_optional_spec_loading() -> None:
    @dg.asset
    def my_asset(): ...

    spec = dg.AssetSpec("other_asset")

    module_fake = build_module_fake("foo", {"my_asset": my_asset, "other_asset": spec})
    assets = load_assets_from_modules([module_fake], key_prefix="prefix")
    assert len(assets) == 1
    assert isinstance(assets[0], dg.AssetsDefinition)
    assert assets[0].key.path == ["prefix", "my_asset"]

    assets = load_assets_from_modules([module_fake], key_prefix="prefix", include_specs=True)
    assert len(assets) == 2
    assert (
        len(
            [
                asset
                for asset in assets
                if isinstance(asset, dg.AssetsDefinition)
                and asset.key.path == ["prefix", "my_asset"]
            ]
        )
        == 1
    )
    assert (
        len(
            [
                asset
                for asset in assets
                if isinstance(asset, dg.AssetSpec) and asset.key.path == ["other_asset"]
            ]
        )
        == 1
    )

    assets = load_assets_from_modules(
        [module_fake], key_prefix="prefix", source_key_prefix="other_prefix", include_specs=True
    )
    assert len(assets) == 2
    assert (
        len(
            [
                asset
                for asset in assets
                if isinstance(asset, dg.AssetsDefinition)
                and asset.key.path == ["prefix", "my_asset"]
            ]
        )
        == 1
    )
    assert (
        len(
            [
                asset
                for asset in assets
                if isinstance(asset, dg.AssetSpec)
                and asset.key.path == ["other_prefix", "other_asset"]
            ]
        )
        == 1
    )
