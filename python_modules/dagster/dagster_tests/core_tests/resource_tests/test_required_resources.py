import pytest
from dagster import (
    AssetMaterialization,
    CompositeSolidDefinition,
    DagsterInstance,
    DagsterType,
    DagsterUnknownResourceError,
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    ResourceDefinition,
    String,
    composite_solid,
    dagster_type_loader,
    dagster_type_materializer,
    execute_pipeline,
    pipeline,
    resource,
    solid,
    usable_as_dagster_type,
)
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.execution.api import execute_run
from dagster.core.storage.type_storage import TypeStoragePlugin
from dagster.core.types.dagster_type import create_any_type


def get_resource_init_pipeline(resources_initted):
    @resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @resource
    def resource_b(_):
        resources_initted["b"] = True
        yield "B"

    @solid(required_resource_keys={"a"})
    def consumes_resource_a(context):
        assert context.resources.a == "A"

    @solid(required_resource_keys={"b"})
    def consumes_resource_b(context):
        assert context.resources.b == "B"

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "a": resource_a,
                    "b": resource_b,
                }
            )
        ],
    )
    def selective_init_test_pipeline():
        consumes_resource_a()
        consumes_resource_b()

    return selective_init_test_pipeline


def test_filter_out_resources():
    @solid(required_resource_keys={"a"})
    def requires_resource_a(context):
        assert context.resources.a
        assert not hasattr(context.resources, "b")

    @solid(required_resource_keys={"b"})
    def requires_resource_b(context):
        assert not hasattr(context.resources, "a")
        assert context.resources.b

    @solid
    def not_resources(context):
        assert not hasattr(context.resources, "a")
        assert not hasattr(context.resources, "b")

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "a": ResourceDefinition.hardcoded_resource("foo"),
                    "b": ResourceDefinition.hardcoded_resource("bar"),
                }
            )
        ],
    )
    def room_of_requirement():
        requires_resource_a()
        requires_resource_b()
        not_resources()

    execute_pipeline(room_of_requirement)


def test_selective_init_resources():
    resources_initted = {}

    assert execute_pipeline(get_resource_init_pipeline(resources_initted)).success

    assert set(resources_initted.keys()) == {"a", "b"}


def test_selective_init_resources_only_a():
    resources_initted = {}

    @resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @resource
    def resource_b(_):
        resources_initted["b"] = True
        yield "B"

    @solid(required_resource_keys={"a"})
    def consumes_resource_a(context):
        assert context.resources.a == "A"

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"a": resource_a, "b": resource_b})])
    def selective_init_test_pipeline():
        consumes_resource_a()

    assert execute_pipeline(selective_init_test_pipeline).success

    assert set(resources_initted.keys()) == {"a"}


def test_execution_plan_subset_strict_resources():
    resources_initted = {}

    instance = DagsterInstance.ephemeral()

    pipeline_def = get_resource_init_pipeline(resources_initted)

    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def,
        step_keys_to_execute=["consumes_resource_b"],
    )

    result = execute_run(InMemoryPipeline(pipeline_def), pipeline_run, instance)

    assert result.success

    assert set(resources_initted.keys()) == {"b"}


def test_solid_selection_strict_resources():
    resources_initted = {}

    selective_init_test_pipeline = get_resource_init_pipeline(resources_initted)

    result = execute_pipeline(
        selective_init_test_pipeline.get_pipeline_subset_def({"consumes_resource_b"})
    )
    assert result.success

    assert set(resources_initted.keys()) == {"b"}


def test_solid_selection_with_aliases_strict_resources():
    resources_initted = {}

    @resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @resource
    def resource_b(_):
        resources_initted["b"] = True
        yield "B"

    @solid(required_resource_keys={"a"})
    def consumes_resource_a(context):
        assert context.resources.a == "A"

    @solid(required_resource_keys={"b"})
    def consumes_resource_b(context):
        assert context.resources.b == "B"

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "a": resource_a,
                    "b": resource_b,
                }
            )
        ],
    )
    def selective_init_test_pipeline():
        consumes_resource_a.alias("alias_for_a")()
        consumes_resource_b()

    result = execute_pipeline(selective_init_test_pipeline.get_pipeline_subset_def({"alias_for_a"}))
    assert result.success

    assert set(resources_initted.keys()) == {"a"}


def create_composite_solid_pipeline(resources_initted):
    @resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "a"

    @resource
    def resource_b(_):
        resources_initted["b"] = True
        yield "B"

    @solid(required_resource_keys={"a"})
    def consumes_resource_a(context):
        assert context.resources.a == "A"

    @solid(required_resource_keys={"b"})
    def consumes_resource_b(context):
        assert context.resources.b == "B"

    @solid
    def consumes_resource_b_error(context):
        assert context.resources.b == "B"

    @composite_solid
    def wraps_a():
        consumes_resource_a()

    @composite_solid
    def wraps_b():
        consumes_resource_b()

    @composite_solid
    def wraps_b_error():
        consumes_resource_b()
        consumes_resource_b_error()

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "a": resource_a,
                    "b": resource_b,
                }
            )
        ],
    )
    def selective_init_composite_test_pipeline():
        wraps_a()
        wraps_b()
        wraps_b_error()

    return selective_init_composite_test_pipeline


def test_solid_selection_strict_resources_within_composite():
    resources_initted = {}

    result = execute_pipeline(
        create_composite_solid_pipeline(resources_initted).get_pipeline_subset_def({"wraps_b"})
    )
    assert result.success

    assert set(resources_initted.keys()) == {"b"}


def test_execution_plan_subset_strict_resources_within_composite():
    resources_initted = {}

    pipeline_def = create_composite_solid_pipeline(resources_initted)

    instance = DagsterInstance.ephemeral()

    pipeline_run = instance.create_run_for_pipeline(
        pipeline_def,
        step_keys_to_execute=["wraps_b.consumes_resource_b"],
    )

    result = execute_run(InMemoryPipeline(pipeline_def), pipeline_run, instance)

    assert result.success

    assert set(resources_initted.keys()) == {"b"}


def test_unknown_resource_composite_error():
    resources_initted = {}

    with pytest.raises(DagsterUnknownResourceError):
        execute_pipeline(
            create_composite_solid_pipeline(resources_initted).get_pipeline_subset_def(
                {"wraps_b_error"}
            )
        )


def test_execution_plan_subset_with_aliases():
    resources_initted = {}

    @resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @resource
    def resource_b(_):
        resources_initted["b"] = True
        yield "B"

    @solid(required_resource_keys={"a"})
    def consumes_resource_a(context):
        assert context.resources.a == "A"

    @solid(required_resource_keys={"b"})
    def consumes_resource_b(context):
        assert context.resources.b == "B"

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "a": resource_a,
                    "b": resource_b,
                }
            )
        ],
    )
    def selective_init_test_pipeline_with_alias():
        consumes_resource_a()
        consumes_resource_b.alias("b_alias")()

    instance = DagsterInstance.ephemeral()

    pipeline_run = instance.create_run_for_pipeline(
        selective_init_test_pipeline_with_alias,
        step_keys_to_execute=["b_alias"],
    )

    result = execute_run(
        InMemoryPipeline(selective_init_test_pipeline_with_alias), pipeline_run, instance
    )

    assert result.success

    assert set(resources_initted.keys()) == {"b"}


def test_custom_type_with_resource_dependent_hydration():
    def define_input_hydration_pipeline(should_require_resources):
        @resource
        def resource_a(_):
            yield "A"

        @dagster_type_loader(
            String, required_resource_keys={"a"} if should_require_resources else set()
        )
        def InputHydration(context, hello):
            assert context.resources.a == "A"
            return CustomType(hello)

        @usable_as_dagster_type(loader=InputHydration)
        class CustomType(str):
            pass

        @solid(input_defs=[InputDefinition("custom_type", CustomType)])
        def input_hydration_solid(context, custom_type):
            context.log.info(custom_type)

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"a": resource_a})])
        def input_hydration_pipeline():
            input_hydration_solid()

        return input_hydration_pipeline

    under_required_pipeline = define_input_hydration_pipeline(should_require_resources=False)
    with pytest.raises(DagsterUnknownResourceError):
        execute_pipeline(
            under_required_pipeline,
            {"solids": {"input_hydration_solid": {"inputs": {"custom_type": "hello"}}}},
        )

    sufficiently_required_pipeline = define_input_hydration_pipeline(should_require_resources=True)
    assert execute_pipeline(
        sufficiently_required_pipeline,
        {"solids": {"input_hydration_solid": {"inputs": {"custom_type": "hello"}}}},
    ).success


def test_resource_dependent_hydration_with_selective_init():
    def get_resource_init_input_hydration_pipeline(resources_initted):
        @resource
        def resource_a(_):
            resources_initted["a"] = True
            yield "A"

        @dagster_type_loader(String, required_resource_keys={"a"})
        def InputHydration(context, hello):
            assert context.resources.a == "A"
            return CustomType(hello)

        @usable_as_dagster_type(loader=InputHydration)
        class CustomType(str):
            pass

        @solid(input_defs=[InputDefinition("custom_type", CustomType)])
        def input_hydration_solid(context, custom_type):
            context.log.info(custom_type)

        @solid(output_defs=[OutputDefinition(CustomType)])
        def source_custom_type(_):
            return CustomType("from solid")

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"a": resource_a})])
        def selective_pipeline():
            input_hydration_solid(source_custom_type())

        return selective_pipeline

    resources_initted = {}
    assert execute_pipeline(get_resource_init_input_hydration_pipeline(resources_initted)).success
    assert set(resources_initted.keys()) == set()


def define_plugin_pipeline(
    should_require_resources=True,
    resources_initted=None,
    compatible_storage=True,
    mode_defines_resource=True,
):
    if resources_initted is None:
        resources_initted = {}

    class CustomStoragePlugin(TypeStoragePlugin):  # pylint: disable=no-init
        @classmethod
        def compatible_with_storage_def(cls, _):
            return compatible_storage

        @classmethod
        def set_intermediate_object(
            cls, intermediate_storage, context, dagster_type, step_output_handle, value
        ):
            assert context.resources.a == "A"
            return intermediate_storage.set_intermediate_object(
                dagster_type, step_output_handle, value
            )

        @classmethod
        def get_intermediate_object(
            cls, intermediate_storage, context, dagster_type, step_output_handle
        ):
            assert context.resources.a == "A"
            return intermediate_storage.get_intermediate_object(dagster_type, step_output_handle)

        @classmethod
        def required_resource_keys(cls):
            return {"a"} if should_require_resources else set()

    @resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    CustomDagsterType = create_any_type(name="CustomType", auto_plugins=[CustomStoragePlugin])

    @solid(output_defs=[OutputDefinition(CustomDagsterType)])
    def output_solid(_context):
        return "hello"

    if mode_defines_resource:
        mode_defs = [ModeDefinition(resource_defs={"a": resource_a})]
    else:
        mode_defs = [ModeDefinition()]

    @pipeline(mode_defs=mode_defs)
    def plugin_pipeline():
        output_solid()

    return plugin_pipeline


def test_custom_type_with_resource_dependent_storage_plugin():
    under_required_pipeline = define_plugin_pipeline(should_require_resources=False)
    with pytest.raises(DagsterUnknownResourceError):
        execute_pipeline(under_required_pipeline, {"intermediate_storage": {"filesystem": {}}})

    resources_initted = {}
    sufficiently_required_pipeline = define_plugin_pipeline(
        should_require_resources=True, resources_initted=resources_initted
    )
    assert execute_pipeline(
        sufficiently_required_pipeline, {"intermediate_storage": {"filesystem": {}}}
    ).success
    assert set(resources_initted.keys()) == set("a")

    resources_initted = {}
    assert execute_pipeline(
        define_plugin_pipeline(resources_initted, compatible_storage=False)
    ).success
    assert set(resources_initted.keys()) == set()


def define_materialization_pipeline(should_require_resources=True, resources_initted=None):
    if resources_initted is None:
        resources_initted = {}

    @resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @dagster_type_materializer(
        String, required_resource_keys={"a"} if should_require_resources else set()
    )
    def materialize(context, *_args, **_kwargs):
        assert context.resources.a == "A"
        return AssetMaterialization("hello")

    CustomDagsterType = create_any_type(name="CustomType", materializer=materialize)

    @solid(output_defs=[OutputDefinition(CustomDagsterType)])
    def output_solid(_context):
        return "hello"

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"a": resource_a})])
    def output_pipeline():
        output_solid()

    return output_pipeline


def test_custom_type_with_resource_dependent_materialization():
    under_required_pipeline = define_materialization_pipeline(should_require_resources=False)
    with pytest.raises(DagsterUnknownResourceError):
        execute_pipeline(
            under_required_pipeline,
            {"solids": {"output_solid": {"outputs": [{"result": "hello"}]}}},
        )

    resources_initted = {}
    sufficiently_required_pipeline = define_materialization_pipeline(
        should_require_resources=True, resources_initted=resources_initted
    )
    res = execute_pipeline(
        sufficiently_required_pipeline,
        {"solids": {"output_solid": {"outputs": [{"result": "hello"}]}}},
    )
    assert res.success
    assert res.result_for_solid("output_solid").output_value() == "hello"
    assert set(resources_initted.keys()) == set("a")

    resources_initted = {}
    assert execute_pipeline(
        define_materialization_pipeline(resources_initted=resources_initted)
    ).success
    assert set(resources_initted.keys()) == set()


def define_composite_materialization_pipeline(
    should_require_resources=True, resources_initted=None
):
    if resources_initted is None:
        resources_initted = {}

    @resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @dagster_type_materializer(
        String, required_resource_keys={"a"} if should_require_resources else set()
    )
    def materialize(context, *_args, **_kwargs):
        assert context.resources.a == "A"
        return AssetMaterialization("hello")

    CustomDagsterType = create_any_type(name="CustomType", materializer=materialize)

    @solid(output_defs=[OutputDefinition(CustomDagsterType)])
    def output_solid(_context):
        return "hello"

    wrap_solid = CompositeSolidDefinition(
        name="wrap_solid",
        solid_defs=[output_solid],
        output_mappings=[OutputDefinition(CustomDagsterType).mapping_from("output_solid")],
    )

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"a": resource_a})])
    def output_pipeline():
        wrap_solid()

    return output_pipeline


def test_custom_type_with_resource_dependent_composite_materialization():
    under_required_pipeline = define_composite_materialization_pipeline(
        should_require_resources=False
    )
    with pytest.raises(DagsterUnknownResourceError):
        execute_pipeline(
            under_required_pipeline,
            {"solids": {"wrap_solid": {"outputs": [{"result": "hello"}]}}},
        )

    sufficiently_required_pipeline = define_composite_materialization_pipeline(
        should_require_resources=True
    )
    assert execute_pipeline(
        sufficiently_required_pipeline,
        {"solids": {"wrap_solid": {"outputs": [{"result": "hello"}]}}},
    ).success

    # test that configured output materialization of the wrapping composite initializes resource
    resources_initted = {}
    assert execute_pipeline(
        define_composite_materialization_pipeline(resources_initted=resources_initted),
        {"solids": {"wrap_solid": {"outputs": [{"result": "hello"}]}}},
    ).success
    assert set(resources_initted.keys()) == set("a")

    # test that configured output materialization of the inner solid initializes resource
    resources_initted = {}
    assert execute_pipeline(
        define_composite_materialization_pipeline(resources_initted=resources_initted),
        {
            "solids": {
                "wrap_solid": {"solids": {"output_solid": {"outputs": [{"result": "hello"}]}}}
            }
        },
    ).success
    assert set(resources_initted.keys()) == set("a")

    # test that no output config will not initialize anything
    resources_initted = {}
    assert execute_pipeline(
        define_composite_materialization_pipeline(resources_initted=resources_initted),
    ).success
    assert set(resources_initted.keys()) == set()


def test_custom_type_with_resource_dependent_type_check():
    def define_type_check_pipeline(should_require_resources):
        @resource
        def resource_a(_):
            yield "A"

        def resource_based_type_check(context, value):
            return context.resources.a == value

        CustomType = DagsterType(
            name="NeedsA",
            type_check_fn=resource_based_type_check,
            required_resource_keys={"a"} if should_require_resources else None,
        )

        @solid(output_defs=[OutputDefinition(CustomType, "custom_type")])
        def custom_type_solid(_):
            return "A"

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"a": resource_a})])
        def type_check_pipeline():
            custom_type_solid()

        return type_check_pipeline

    under_required_pipeline = define_type_check_pipeline(should_require_resources=False)
    with pytest.raises(DagsterUnknownResourceError):
        execute_pipeline(under_required_pipeline)

    sufficiently_required_pipeline = define_type_check_pipeline(should_require_resources=True)
    assert execute_pipeline(sufficiently_required_pipeline).success


def test_resource_no_version():
    @resource
    def no_version_resource(_):
        pass

    assert no_version_resource.version == None


def test_resource_passed_version():
    @resource(version="42")
    def passed_version_resource(_):
        pass

    assert passed_version_resource.version == "42"


def test_type_missing_resource_fails():
    def resource_based_type_check(context, value):
        return context.resources.a == value

    CustomType = DagsterType(
        name="NeedsA",
        type_check_fn=resource_based_type_check,
        required_resource_keys={"a"},
    )

    @solid(output_defs=[OutputDefinition(CustomType, "custom_type")])
    def custom_type_solid(_):
        return "A"

    with pytest.raises(DagsterInvalidDefinitionError, match='required by type "NeedsA"'):

        @pipeline
        def _type_check_pipeline():
            custom_type_solid()


def test_loader_missing_resource_fails():
    @dagster_type_loader(String, required_resource_keys={"a"})
    def InputHydration(context, hello):
        assert context.resources.a == "A"
        return CustomType(hello)

    @usable_as_dagster_type(loader=InputHydration)
    class CustomType(str):
        pass

    @solid(input_defs=[InputDefinition("_custom_type", CustomType)])
    def custom_type_solid(_, _custom_type):
        return "A"

    with pytest.raises(
        DagsterInvalidDefinitionError, match='required by the loader on type "CustomType"'
    ):

        @pipeline
        def _type_check_pipeline():
            custom_type_solid()


def test_materialize_missing_resource_fails():
    @dagster_type_materializer(String, required_resource_keys={"a"})
    def materialize(context, *_args, **_kwargs):
        assert context.resources.a == "A"
        return AssetMaterialization("hello")

    CustomType = create_any_type(name="CustomType", materializer=materialize)

    @solid(output_defs=[OutputDefinition(CustomType, "custom_type")])
    def custom_type_solid(_):
        return "A"

    with pytest.raises(
        DagsterInvalidDefinitionError, match='required by the materializer on type "CustomType"'
    ):

        @pipeline
        def _type_check_pipeline():
            custom_type_solid()


def test_plugin_missing_resource_fails():
    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=r'required by the plugin "CustomStoragePlugin" on type "CustomType" \(used with storages',
    ):
        define_plugin_pipeline(mode_defines_resource=False)

    # works since storages are not compatible with plugin
    define_plugin_pipeline(mode_defines_resource=False, compatible_storage=False)
