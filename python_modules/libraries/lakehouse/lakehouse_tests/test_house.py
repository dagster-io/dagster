import pytest
from lakehouse import SourceAsset, computed_asset

from dagster import execute_pipeline
from dagster.check import CheckError


def _assert_input_defs(solid_def, expected):
    assert len(solid_def.input_defs) == len(expected)
    assert sorted(expected) == sorted(
        (input_def.dagster_type, input_def.name) for input_def in solid_def.input_defs
    )


def _assert_output_def(solid_def, expected_dagster_type, expected_name):
    assert len(solid_def.output_defs) == 1
    output_def = solid_def.output_defs[0]
    assert output_def.dagster_type == expected_dagster_type
    assert output_def.name == expected_name


def test_get_computed_asset_solid_def_name(basic_lakehouse):
    @computed_asset(storage_key='filesystem', path=('a', 'b', 'c'))
    def some_asset() -> int:
        return 1

    solid_def = basic_lakehouse.get_computed_asset_solid_def(some_asset, [])
    assert solid_def.name == 'a__b__c'


def test_get_computed_asset_solid_def_no_deps(basic_lakehouse):
    @computed_asset(storage_key='storage1')
    def some_asset() -> int:
        return 1

    solid_def = basic_lakehouse.get_computed_asset_solid_def(some_asset, [])
    assert solid_def.required_resource_keys == {'storage1'}
    _assert_input_defs(solid_def, [])
    _assert_output_def(solid_def, some_asset.dagster_type, 'result')


def test_get_computed_asset_solid_def_with_source_deps(basic_lakehouse):
    source_asset1 = SourceAsset(storage_key='storage1', path=('a', 'b'))
    source_asset2 = SourceAsset(storage_key='storage1', path=('a', 'c'))

    @computed_asset(storage_key='storage1', input_assets=[source_asset1, source_asset2])
    def some_asset(source1: int, source2: int) -> int:
        return source1 + source2

    solid_def = basic_lakehouse.get_computed_asset_solid_def(some_asset, [])
    assert solid_def.required_resource_keys == {'storage1'}
    _assert_input_defs(solid_def, [])
    _assert_output_def(solid_def, some_asset.dagster_type, 'result')


def test_get_computed_asset_solid_def_with_source_deps_multiple_storages(basic_lakehouse):
    source_asset1 = SourceAsset(storage_key='storage1', path=('a', 'b'))
    source_asset2 = SourceAsset(storage_key='storage2', path=('a', 'c'))

    @computed_asset(storage_key='storage1', input_assets=[source_asset1, source_asset2])
    def some_asset(source1: int, source2: int) -> int:
        return source1 + source2

    solid_def = basic_lakehouse.get_computed_asset_solid_def(some_asset, [])
    assert solid_def.required_resource_keys == {'storage1', 'storage2'}
    _assert_input_defs(solid_def, [])
    _assert_output_def(solid_def, some_asset.dagster_type, 'result')


def test_get_computed_asset_solid_def_with_computed_asset_deps(basic_lakehouse):
    @computed_asset(storage_key='storage1')
    def dep_asset1() -> int:
        pass

    @computed_asset(storage_key='storage1')
    def dep_asset2() -> int:
        pass

    @computed_asset(storage_key='storage2', input_assets=[dep_asset1, dep_asset2])
    def some_asset(source1: int, source2: int) -> int:
        return source1 + source2

    solid_def = basic_lakehouse.get_computed_asset_solid_def(some_asset, [dep_asset1, dep_asset2])
    assert solid_def.required_resource_keys == {'storage1', 'storage2'}
    _assert_input_defs(
        solid_def,
        [(dep_asset1.dagster_type, 'dep_asset1'), (dep_asset2.dagster_type, 'dep_asset2')],
    )
    _assert_output_def(solid_def, some_asset.dagster_type, 'result')


def test_build_pipeline_definition_missing_storage(basic_lakehouse):
    @computed_asset(storage_key='storage3')
    def return_one_asset() -> int:
        return 1

    with pytest.raises(CheckError):
        basic_lakehouse.build_pipeline_definition('some_pipeline', [return_one_asset])


def test_build_pipeline_definition_missing_output_policy(basic_lakehouse):
    @computed_asset(storage_key='storage1')
    def str_asset() -> str:
        return ''

    with pytest.raises(CheckError):
        basic_lakehouse.build_pipeline_definition('some_pipeline', [str_asset])


def test_build_pipeline_definition_missing_input_policy(basic_lakehouse):
    source_asset = SourceAsset(storage_key='storage1', path=('a', 'b'))

    @computed_asset(storage_key='storage1', input_assets=[source_asset])
    def some_asset(source: str) -> int:
        return int(source)

    with pytest.raises(CheckError):
        basic_lakehouse.build_pipeline_definition('some_pipeline', [some_asset])


def test_build_and_execute_pipeline(basic_lakehouse_and_storages):
    basic_lakehouse, storage1, storage2 = basic_lakehouse_and_storages

    @computed_asset(storage_key='storage1')
    def return_one_asset() -> int:
        return 1

    @computed_asset(storage_key='storage2')
    def return_two_asset() -> int:
        return 2

    @computed_asset(storage_key='storage2', input_assets=[return_one_asset, return_two_asset])
    def add_asset(return_one: int, return_two: int) -> int:
        return return_one + return_two

    pipeline = basic_lakehouse.build_pipeline_definition(
        'some_pipeline', [return_one_asset, return_two_asset, add_asset]
    )
    execute_pipeline(pipeline, mode='dev')
    assert storage1.the_dict[('return_one_asset',)] == 1
    assert ('return_one_asset',) not in storage2.the_dict
    assert storage2.the_dict[('return_two_asset',)] == 2
    assert ('return_two_asset',) not in storage1.the_dict
    assert storage2.the_dict[('add_asset',)] == 3
    assert ('add_asset',) not in storage1.the_dict
