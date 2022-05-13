import pytest

from dagster import (
    AssetGroup,
    ResourceDefinition,
    asset,
    fs_io_manager,
    io_manager,
    repository,
    resource,
    with_resources,
)

#####################################
# Resource definitions on assets
#####################################


def test_with_resources():
    @resource
    def my_resource():
        ...

    @asset(resource_defs={"foo": my_resource})
    def asset1():
        ...

    @asset(required_resource_keys={"foo"})
    def asset2():
        ...

    assert (
        asset1.resource_defs
        == with_resources([asset2], resource_defs={"foo": my_resource})[0].resource_defs
    )


def test_different_resource_different_asset_keys():
    @asset(resource_defs={"foo": ResourceDefinition.string_resource()})
    def asset1(context):
        assert context.foo == "abc"

    @asset(resource_defs={"bar": ResourceDefinition.string_resource()})
    def asset2(context):
        assert context.foo == "xyz"

    assert (
        AssetGroup([asset1, asset2])
        .materialize(run_config={"resources": {"foo": {"config": "abc"}, "bar": {"config": "xyz"}}})
        .success
    )


def test_config_same_resource_multiple_assets():
    my_string_resource = ResourceDefinition.string_resource()

    @asset(resource_defs={"foo": my_string_resource})
    def asset1(context):
        assert context.foo == "abc"

    @asset(resource_defs={"foo": my_string_resource})
    def asset2(context):
        assert context.foo == "abc"

    assert (
        AssetGroup([asset1, asset2])
        .materialize(run_config={"resources": {"foo": {"config": "abc"}}})
        .success
    )


def test_different_resource_multiple_assets():
    @resource
    def resource1():
        ...

    @resource
    def resource2():
        ...

    @asset(resource_defs={"foo": resource1})
    def asset1(context):
        ...

    @asset(resource_defs={"foo": resource2})
    def asset2(context):
        ...

    group = AssetGroup([asset1, asset2])
    assert group.materialize(selection=["asset1"]).success
    assert group.materialize(selection=["asset2"]).success
    with pytest.raises(
        match="blah blah different resource definitions for the same resource key. plz use a different resource key."
    ):
        group.materialize()


def test_io_manager_keys():
    @io_manager(config_schema=str)
    def my_configurable_io_manager():
        ...

    @asset(resource_defs={"foo": my_configurable_io_manager}, io_manager_key="foo")
    def asset1(context):
        ...

    @asset(resource_defs={"foo": my_configurable_io_manager}, io_manager_key="foo")
    def asset2(context):
        ...

    AssetGroup([asset1, asset2]).materialize(run_config={"resources": {"foo": {"config": "abc"}}})


def test_unsatisfied_resource_requirement():
    @asset(resource_defs={"foo": ResourceDefinition.none_resource()})
    def asset1(context):
        ...

    @asset(required_resource_keys={"foo"})
    def asset2(context):
        ...

    with pytest.raises(
        match="blah blah asset2 doesn't have a definition for required resource foo"
    ):
        AssetGroup([asset1, asset2]).materialize()

    with pytest.raises(
        match="blah blah asset2 doesn't have a definition for required resource foo"
    ):

        @repository
        def repo():
            return [[asset1, asset2]]


#####################################
# IO manager definitions on assets
# When you directly provide an IO manager definition, there is effectively no resource key involved.
#####################################


def test_io_manager_def_on_asset():
    @asset(io_manager_def=fs_io_manager.configured({"base_dir": "abc"}))
    def asset1():
        ...

    @asset(io_manager_def=fs_io_manager.configured({"base_dir": "xyz"}))
    def asset2():
        ...

    assert AssetGroup([asset1, asset2]).materialize().success


def test_io_manager_def_on_asset_config_schema():
    """
    Directly-provided IO managers can't be configured at run time because there's no resource key to
    configure them with.
    """

    @io_manager(config_schema={"required_config_param": str})
    def my_configurable_io_manager():
        ...

    with pytest.raises(
        match="blah blah IO managers specified directly on asset cannot require config"
    ):

        @asset(io_manager_def=my_configurable_io_manager)
        def asset1():
            ...


def test_io_manager_def_on_asset_required_resources():
    @io_manager(required_resource_keys={"abc"})
    def my_io_manager():
        ...

    @asset(
        io_manager_def=my_io_manager, resource_defs={"abc": ResourceDefinition.string_resource()}
    )
    def asset1():
        ...

    AssetGroup([asset1]).materialize().success
