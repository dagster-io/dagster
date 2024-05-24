import warnings

import pytest
from dagster import (
    AssetKey,
    Definitions,
    IOManager,
    IOManagerDefinition,
    ResourceDefinition,
    build_asset_context,
    execute_job,
    io_manager,
    mem_io_manager,
    reconstructable,
    resource,
)
from dagster._core.definitions import AssetsDefinition, SourceAsset, asset
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.errors import (
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
)
from dagster._core.execution.with_resources import with_resources
from dagster._core.storage.fs_io_manager import PickledObjectFilesystemIOManager
from dagster._core.storage.mem_io_manager import InMemoryIOManager
from dagster._core.test_utils import environ, instance_for_test


@pytest.fixture
def instance():
    with instance_for_test() as instance:
        yield instance


def test_assets_direct():
    @asset(required_resource_keys={"foo"})
    def the_asset(context):
        assert context.resources.foo == "blah"
        return 5

    in_mem = InMemoryIOManager()

    @io_manager
    def the_io_manager():
        return in_mem

    transformed_asset = with_resources(
        [the_asset],
        {"foo": ResourceDefinition.hardcoded_resource("blah"), "io_manager": the_io_manager},
    )[0]
    assert isinstance(transformed_asset, AssetsDefinition)

    # When an io manager is provided with the generic key, that generic key is
    # used in the resource def dictionary.
    assert transformed_asset.node_def.output_defs[0].io_manager_key == "io_manager"

    assert materialize([transformed_asset]).success
    assert next(iter(in_mem.values.values())) == 5


def test_asset_requires_io_manager_key():
    @asset(io_manager_key="the_manager")
    def the_asset():
        return 5

    in_mem = InMemoryIOManager()

    @io_manager
    def the_io_manager():
        return in_mem

    transformed_asset = with_resources(
        [the_asset],
        {"foo": ResourceDefinition.hardcoded_resource("blah"), "the_manager": the_io_manager},
    )[0]
    assert isinstance(transformed_asset, AssetsDefinition)

    assert materialize([transformed_asset]).success
    assert next(iter(in_mem.values.values())) == 5


def test_assets_direct_resource_conflicts():
    @asset(required_resource_keys={"foo"})
    def the_asset():
        pass

    @asset(required_resource_keys={"foo"})
    def other_asset():
        pass

    transformed_asset = with_resources(
        [the_asset],
        {"foo": ResourceDefinition.hardcoded_resource("blah")},
    )[0]

    other_transformed_asset = with_resources(
        [other_asset],
        {"foo": ResourceDefinition.hardcoded_resource("blah")},
    )[0]

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "Conflicting versions of resource with key 'foo' were provided to different assets."
            " When constructing a job, all resource definitions provided to assets must match by"
            " reference equality for a given key."
        ),
    ):
        materialize([transformed_asset, other_transformed_asset])


def test_source_assets_no_key_provided():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @io_manager
    def the_manager():
        return MyIOManager()

    my_source_asset = SourceAsset(key=AssetKey("my_source_asset"))

    @asset
    def my_derived_asset(my_source_asset):
        return my_source_asset + 4

    transformed_source, transformed_derived = with_resources(
        [my_source_asset, my_derived_asset], resource_defs={"io_manager": the_manager}
    )

    # When an io manager definition is provided using the generic key, that
    # generic key is used as the io manager key for the source asset.
    assert transformed_source.get_io_manager_key() == "io_manager"

    result = materialize([transformed_derived, transformed_source], selection=[transformed_derived])
    assert result.success
    assert result.output_for_node("my_derived_asset") == 9


def test_source_assets_key_provided():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @io_manager
    def the_manager():
        return MyIOManager()

    my_source_asset = SourceAsset(key=AssetKey("my_source_asset"), io_manager_key="the_manager")

    @asset
    def my_derived_asset(my_source_asset):
        return my_source_asset + 4

    transformed_source, transformed_derived = with_resources(
        [my_source_asset, my_derived_asset], resource_defs={"the_manager": the_manager}
    )

    # When an io manager definition is provided using the generic key, that
    # generic key is used as the io manager key for the source asset.
    assert transformed_source.get_io_manager_key() == "the_manager"

    result = materialize([transformed_derived, transformed_source], selection=[transformed_derived])
    assert result.success
    assert result.output_for_node("my_derived_asset") == 9


def test_source_assets_manager_def_provided():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @io_manager
    def the_manager():
        return MyIOManager()

    my_source_asset = SourceAsset(key=AssetKey("my_source_asset"), io_manager_def=the_manager)

    @asset
    def my_derived_asset(my_source_asset):
        return my_source_asset + 4

    transformed_source, transformed_derived = with_resources(
        [my_source_asset, my_derived_asset], resource_defs={"io_manager": mem_io_manager}
    )

    # When an io manager definition has already been provided, it will use an
    # override key.
    assert transformed_source.io_manager_def == the_manager

    result = materialize([transformed_derived, transformed_source], selection=[transformed_derived])
    assert result.success
    assert result.output_for_node("my_derived_asset") == 9


def test_asset_def_partial_application():
    @asset(required_resource_keys={"foo", "bar"})
    def the_asset():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="resource with key 'bar' required by op 'the_asset' was not provided.",
    ):
        with_resources([the_asset], {"foo": ResourceDefinition.hardcoded_resource("foo")})


def test_source_asset_no_manager_def():
    the_source_asset = SourceAsset(key=AssetKey("my_source_asset"))
    # Ensure we don't error when no manager def is provided for default key,
    # because io manager def can utilize default.
    with_resources([the_source_asset], {})

    the_source_asset = SourceAsset(key=AssetKey("my_source_asset"), io_manager_key="foo")
    # Ensure error when io manager key is provided and resources don't satisfy.
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "io manager with key 'foo' required by SourceAsset with key \\[\"my_source_asset\"\\]"
            " was not provided"
        ),
    ):
        with_resources([the_source_asset], {})


def test_asset_transitive_resource_deps():
    @resource(required_resource_keys={"foo"})
    def the_resource(context):
        assert context.resources.foo == "bar"

    @asset(resource_defs={"the_resource": the_resource})
    def the_asset():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "resource with key 'foo' required by resource with key 'the_resource' was not provided"
        ),
    ):
        with_resources([the_asset], {})

    transformed_asset = with_resources(
        [the_asset], {"foo": ResourceDefinition.hardcoded_resource("bar")}
    )[0]

    assert materialize([transformed_asset]).success


def test_asset_io_manager_transitive_dependencies():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @io_manager(required_resource_keys={"the_resource"})
    def the_manager():
        return MyIOManager()

    @asset(io_manager_def=the_manager)
    def the_asset():
        pass

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "resource with key 'the_resource' required by resource with key 'the_asset__io_manager'"
            " was not provided."
        ),
    ):
        with_resources([the_asset], resource_defs={})

    @resource(required_resource_keys={"foo"})
    def the_resource(context):
        assert context.resources.foo == "bar"

    with pytest.raises(
        DagsterInvariantViolationError,
        match=(
            "Resource with key 'foo' required by resource with key 'the_resource', but not"
            " provided."
        ),
    ):
        with_resources([the_asset], resource_defs={"the_resource": the_resource})

    transformed_assets = with_resources(
        [the_asset],
        resource_defs={
            "the_resource": the_resource,
            "foo": ResourceDefinition.hardcoded_resource("bar"),
        },
    )
    assert materialize(transformed_assets).success


def test_source_asset_partial_resources():
    class MyIOManager(IOManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            return 5

    @io_manager(required_resource_keys={"foo"})
    def the_manager(context):
        assert context.resources.foo == "blah"
        return MyIOManager()

    my_source_asset = SourceAsset(key=AssetKey("my_source_asset"), io_manager_def=the_manager)

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "resource with key 'foo' required by resource with key 'my_source_asset__io_manager'"
            " was not provided"
        ),
    ):
        with_resources([my_source_asset], resource_defs={})

    @resource(required_resource_keys={"bar"})
    def foo_resource(context):
        return context.resources.bar

    with pytest.raises(
        DagsterInvariantViolationError,
        match="Resource with key 'bar' required by resource with key 'foo', but not provided.",
    ):
        with_resources([my_source_asset], resource_defs={"foo": foo_resource})

    transformed_source = with_resources(
        [my_source_asset],
        resource_defs={"foo": foo_resource, "bar": ResourceDefinition.hardcoded_resource("blah")},
    )[0]

    @asset
    def my_derived_asset(my_source_asset):
        return my_source_asset + 4

    result = materialize([my_derived_asset, transformed_source], selection=[my_derived_asset])
    assert result.success
    assert result.output_for_node("my_derived_asset") == 9


def test_asset_circular_resource_dependency():
    @asset(required_resource_keys={"foo"})
    def the_asset():
        pass

    @resource(required_resource_keys={"bar"})
    def foo():
        pass

    @resource(required_resource_keys={"foo"})
    def bar():
        pass

    with pytest.raises(
        DagsterInvariantViolationError, match='Resource key "bar" transitively depends on itself.'
    ):
        with_resources([the_asset], resource_defs={"foo": foo, "bar": bar})


def get_resource_and_asset_for_config_tests():
    @asset(required_resource_keys={"foo", "bar"})
    def the_asset(context):
        assert context.resources.foo == "blah"
        assert context.resources.bar == "baz"

    @resource(config_schema=str)
    def the_resource(context):
        return context.resource_config

    return the_asset, the_resource


def test_config():
    the_asset, the_resource = get_resource_and_asset_for_config_tests()

    transformed_asset = with_resources(
        [the_asset],
        resource_defs={"foo": the_resource, "bar": the_resource},
        resource_config_by_key={"foo": {"config": "blah"}, "bar": {"config": "baz"}},
    )[0]

    transformed_asset(build_asset_context())


def test_config_not_satisfied():
    the_asset, the_resource = get_resource_and_asset_for_config_tests()

    transformed_asset = with_resources(
        [the_asset],
        resource_defs={"foo": the_resource, "bar": the_resource},
    )[0]

    assert materialize(
        [transformed_asset],
        run_config={"resources": {"foo": {"config": "blah"}, "bar": {"config": "baz"}}},
    ).success


def test_bad_key_provided():
    the_asset, the_resource = get_resource_and_asset_for_config_tests()

    transformed_asset = with_resources(
        [the_asset],
        resource_defs={"foo": the_resource, "bar": the_resource},
        resource_config_by_key={
            "foo": {"config": "blah"},
            "bar": {"config": "baz"},
            "bad": "whatever",
        },
    )[0]

    transformed_asset(build_asset_context())


def test_bad_config_provided():
    the_asset, the_resource = get_resource_and_asset_for_config_tests()

    with pytest.raises(
        DagsterInvalidConfigError, match="Error when applying config for resource with key 'foo'"
    ):
        with_resources(
            [the_asset],
            resource_defs={"foo": the_resource, "bar": the_resource},
            resource_config_by_key={
                "foo": {"config": object()},
            },
        )

    with pytest.raises(
        DagsterInvalidInvocationError, match="Error with config for resource key 'foo'"
    ):
        with_resources(
            [the_asset],
            resource_defs={"foo": the_resource, "bar": the_resource},
            resource_config_by_key={
                "foo": "bad",
            },
        )


def test_overlapping_io_manager_asset():
    @io_manager
    def the_io_manager():
        pass

    @asset(io_manager_def=the_io_manager)
    def the_asset():
        pass

    # Allow a default io manager to be passed in without causing an error
    with_resources([the_asset], resource_defs={"io_manager": mem_io_manager})

    # Changing the specific affected key causes an error
    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            r"AssetsDefinition with key \[\"the_asset\"\] has conflicting resource definitions with"
            r" provided resources for the following keys: the_asset__io_manager. Either remove the"
            r" existing resources from the asset or change the resource keys so that they don't"
            r" overlap."
        ),
    ):
        with_resources([the_asset], resource_defs={"the_asset__io_manager": mem_io_manager})


def test_overlapping_resources_asset():
    foo_resource = ResourceDefinition.hardcoded_resource("blah")

    @asset(resource_defs={"foo": foo_resource})
    def the_asset():
        pass

    # Even if resource defs match by reference equality, we error
    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            r"AssetsDefinition with key \[\"the_asset\"\] has conflicting resource definitions with"
            r" provided resources for the following keys: foo. Either remove the existing resources"
            r" from the asset or change the resource keys so that they don't overlap."
        ),
    ):
        with_resources(
            [the_asset],
            resource_defs={"foo": foo_resource},
        )

    # Resource def doesn't match by reference equality, error
    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            r"AssetsDefinition with key \[\"the_asset\"\] has conflicting resource definitions with"
            r" provided resources for the following keys: foo. Either remove the existing resources"
            r" from the asset or change the resource keys so that they don't overlap."
        ),
    ):
        with_resources(
            [the_asset], resource_defs={"foo": ResourceDefinition.hardcoded_resource("diff_ref")}
        )


def test_overlapping_io_manager_source_asset():
    @io_manager
    def the_io_manager():
        pass

    the_asset = SourceAsset(key=AssetKey("the_asset"), io_manager_def=the_io_manager)

    # Allow a default io manager to be passed in without causing an error
    with_resources([the_asset], resource_defs={"io_manager": mem_io_manager})

    # Changing the specific affected key causes an error
    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            r"SourceAsset with key AssetKey\(\['the_asset'\]\) has conflicting resource definitions"
            r" with provided resources for the following keys: \['the_asset__io_manager'\]. Either"
            r" remove the existing resources from the asset or change the resource keys so that"
            r" they don't overlap."
        ),
    ):
        with_resources([the_asset], resource_defs={"the_asset__io_manager": mem_io_manager})


def test_overlapping_resources_source_asset():
    foo_resource = ResourceDefinition.hardcoded_resource("blah")

    @io_manager(required_resource_keys={"foo"})
    def the_io_manager():
        pass

    the_asset = SourceAsset(
        key=AssetKey("the_asset"),
        io_manager_def=the_io_manager,
        resource_defs={"foo": foo_resource},
    )

    # If resource defs match by reference equality, we error
    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            r"SourceAsset with key AssetKey\(\['the_asset'\]\) has conflicting resource definitions"
            r" with provided resources for the following keys: \['foo'\]. Either remove the"
            r" existing resources from the asset or change the resource keys so that they don't"
            r" overlap."
        ),
    ):
        with_resources(
            [the_asset],
            resource_defs={"foo": foo_resource},
        )

    # Resource def doesn't match by reference equality, error
    with pytest.raises(
        DagsterInvalidInvocationError,
        match=(
            r"SourceAsset with key AssetKey\(\['the_asset'\]\) has conflicting resource definitions"
            r" with provided resources for the following keys: \['foo'\]. Either remove the"
            r" existing resources from the asset or change the resource keys so that they don't"
            r" overlap."
        ),
    ):
        with_resources(
            [the_asset], resource_defs={"foo": ResourceDefinition.hardcoded_resource("diff_ref")}
        )


def test_with_resources_no_exp_warnings():
    @asset(required_resource_keys={"foo"})
    def blah():
        pass

    @io_manager
    def the_manager():
        pass

    my_source_asset = SourceAsset(key=AssetKey("my_source_asset"), io_manager_key="the_manager")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with_resources(
            [blah, my_source_asset],
            {"foo": ResourceDefinition.hardcoded_resource("something"), "the_manager": the_manager},
        )


def test_bare_resource_on_with_resources():
    class BareObjectResource:
        pass

    executed = {}

    @asset(required_resource_keys={"bare_resource"})
    def blah(context):
        assert context.resources.bare_resource
        executed["yes"] = True

    bound_assets = with_resources([blah], {"bare_resource": BareObjectResource()})
    defs = Definitions(assets=bound_assets)
    defs.get_implicit_global_asset_job_def().execute_in_process()
    assert executed["yes"]


class FooIoManager(PickledObjectFilesystemIOManager):
    def __init__(self):
        super().__init__(base_dir="/tmp/dagster/foo-io-manager")


io_manager_resource_fn = lambda _: FooIoManager()
foo_io_manager_def = IOManagerDefinition(
    resource_fn=io_manager_resource_fn,
    config_schema={},
)


def create_asset_job():
    @asset
    def my_derived_asset():
        return 4

    return Definitions(
        assets=[my_derived_asset], jobs=[define_asset_job("the_job", [my_derived_asset])]
    ).get_job_def("the_job")


def test_source_asset_default_io_manager(instance):
    with environ(
        {
            "DAGSTER_DEFAULT_IO_MANAGER_MODULE": (
                "dagster_tests.core_tests.resource_tests.test_with_resources"
            ),
            "DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE": "foo_io_manager_def",
        }
    ):
        assert execute_job(reconstructable(create_asset_job), instance).success

    with environ(
        {
            "DAGSTER_DEFAULT_IO_MANAGER_MODULE": (
                "dagster_tests.core_tests.resource_tests.fake_file"
            ),
            "DAGSTER_DEFAULT_IO_MANAGER_ATTRIBUTE": "foo_io_manager_def",
        }
    ):
        assert not execute_job(reconstructable(create_asset_job), instance).success
