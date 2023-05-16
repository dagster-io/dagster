from typing import Dict

import pytest
from dagster import (
    DagsterType,
    DagsterUnknownResourceError,
    In,
    Out,
    ResourceDefinition,
    String,
    dagster_type_loader,
    graph,
    job,
    op,
    repository,
    resource,
    usable_as_dagster_type,
)
from dagster._core.definitions.configurable import configured
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvalidSubsetError


def get_resource_init_job(resources_initted: Dict[str, bool]) -> JobDefinition:
    @resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @resource
    def resource_b(_):
        resources_initted["b"] = True
        yield "B"

    @op(required_resource_keys={"a"})
    def consumes_resource_a(context):
        assert context.resources.a == "A"

    @op(required_resource_keys={"b"})
    def consumes_resource_b(context):
        assert context.resources.b == "B"

    @job(
        resource_defs={
            "a": resource_a,
            "b": resource_b,
        },
    )
    def selective_init_test_job():
        consumes_resource_a()
        consumes_resource_b()

    return selective_init_test_job


def test_filter_out_resources():
    @op(required_resource_keys={"a"})
    def requires_resource_a(context):
        assert context.resources.a
        assert not hasattr(context.resources, "b")

    @op(required_resource_keys={"b"})
    def requires_resource_b(context):
        assert not hasattr(context.resources, "a")
        assert context.resources.b

    @op
    def not_resources(context):
        assert not hasattr(context.resources, "a")
        assert not hasattr(context.resources, "b")

    @job(
        resource_defs={
            "a": ResourceDefinition.hardcoded_resource("foo"),
            "b": ResourceDefinition.hardcoded_resource("bar"),
        },
    )
    def room_of_requirement():
        requires_resource_a()
        requires_resource_b()
        not_resources()

    room_of_requirement.execute_in_process()


def test_selective_init_resources():
    resources_initted = {}

    assert get_resource_init_job(resources_initted).execute_in_process().success

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

    @op(required_resource_keys={"a"})
    def consumes_resource_a(context):
        assert context.resources.a == "A"

    @job(resource_defs={"a": resource_a, "b": resource_b})
    def selective_init_test_job():
        consumes_resource_a()

    assert selective_init_test_job.execute_in_process().success

    assert set(resources_initted.keys()) == {"a"}


def test_execution_plan_subset_strict_resources():
    resources_initted = {}

    job_def = get_resource_init_job(resources_initted)

    result = job_def.execute_in_process(op_selection=["consumes_resource_b"])

    assert result.success

    assert set(resources_initted.keys()) == {"b"}


def test_op_selection_strict_resources():
    resources_initted = {}

    selective_init_test_job = get_resource_init_job(resources_initted)

    result = selective_init_test_job.execute_in_process(op_selection=["consumes_resource_b"])
    assert result.success

    assert set(resources_initted.keys()) == {"b"}


def test_op_selection_with_aliases_strict_resources():
    resources_initted = {}

    @resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @resource
    def resource_b(_):
        resources_initted["b"] = True
        yield "B"

    @op(required_resource_keys={"a"})
    def consumes_resource_a(context):
        assert context.resources.a == "A"

    @op(required_resource_keys={"b"})
    def consumes_resource_b(context):
        assert context.resources.b == "B"

    @job(
        resource_defs={
            "a": resource_a,
            "b": resource_b,
        },
    )
    def selective_init_test_job():
        consumes_resource_a.alias("alias_for_a")()
        consumes_resource_b()

    result = selective_init_test_job.execute_in_process(op_selection=["alias_for_a"])
    assert result.success

    assert set(resources_initted.keys()) == {"a"}


def create_nested_graph_job(resources_initted: Dict[str, bool]) -> JobDefinition:
    @resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @resource
    def resource_b(_):
        resources_initted["b"] = True
        yield "B"

    @op(required_resource_keys={"a"})
    def consumes_resource_a(context):
        assert context.resources.a == "A"

    @op(required_resource_keys={"b"})
    def consumes_resource_b(context):
        assert context.resources.b == "B"

    @op
    def consumes_resource_b_error(context):
        assert context.resources.b == "B"

    @graph
    def wraps_a():
        consumes_resource_a()

    @graph
    def wraps_b():
        consumes_resource_b()

    @graph
    def wraps_b_error():
        consumes_resource_b()
        consumes_resource_b_error()

    @job(
        resource_defs={
            "a": resource_a,
            "b": resource_b,
        },
    )
    def selective_init_composite_test_job():
        wraps_a()
        wraps_b()
        wraps_b_error()

    return selective_init_composite_test_job


def test_op_selection_strict_resources_within_composite():
    resources_initted = {}

    result = create_nested_graph_job(resources_initted).execute_in_process(op_selection=["wraps_b"])
    assert result.success

    assert set(resources_initted.keys()) == {"b"}


def test_execution_plan_subset_strict_resources_within_composite():
    resources_initted = {}

    assert (
        create_nested_graph_job(resources_initted)
        .execute_in_process(op_selection=["wraps_b.consumes_resource_b"])
        .success
    )

    assert set(resources_initted.keys()) == {"b"}


def test_unknown_resource_composite_error():
    resources_initted = {}

    with pytest.raises(DagsterUnknownResourceError):
        create_nested_graph_job(resources_initted).execute_in_process(
            op_selection=["wraps_b_error"]
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

    @op(required_resource_keys={"a"})
    def consumes_resource_a(context):
        assert context.resources.a == "A"

    @op(required_resource_keys={"b"})
    def consumes_resource_b(context):
        assert context.resources.b == "B"

    @job(
        resource_defs={
            "a": resource_a,
            "b": resource_b,
        },
    )
    def selective_init_test_job_with_alias():
        consumes_resource_a()
        consumes_resource_b.alias("b_alias")()

    assert selective_init_test_job_with_alias.execute_in_process(op_selection=["b_alias"]).success

    assert set(resources_initted.keys()) == {"b"}


def test_custom_type_with_resource_dependent_hydration():
    def define_input_hydration_job(should_require_resources):
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

        @op(ins={"custom_type": In(CustomType)})
        def input_hydration_op(context, custom_type):
            context.log.info(custom_type)

        @job(resource_defs={"a": resource_a})
        def input_hydration_job():
            input_hydration_op()

        return input_hydration_job

    under_required_job = define_input_hydration_job(should_require_resources=False)
    with pytest.raises(DagsterUnknownResourceError):
        under_required_job.execute_in_process(
            {"ops": {"input_hydration_op": {"inputs": {"custom_type": "hello"}}}},
        )

    sufficiently_required_job = define_input_hydration_job(should_require_resources=True)
    assert sufficiently_required_job.execute_in_process(
        {"ops": {"input_hydration_op": {"inputs": {"custom_type": "hello"}}}},
    ).success


def test_resource_dependent_hydration_with_selective_init():
    def get_resource_init_input_hydration_job(resources_initted):
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

        @op(ins={"custom_type": In(CustomType)})
        def input_hydration_op(context, custom_type):
            context.log.info(custom_type)

        @op(out=Out(CustomType))
        def source_custom_type(_):
            return CustomType("from solid")

        @job(resource_defs={"a": resource_a})
        def selective_job():
            input_hydration_op(source_custom_type())

        return selective_job

    resources_initted = {}
    assert get_resource_init_input_hydration_job(resources_initted).execute_in_process().success
    assert set(resources_initted.keys()) == set()


def test_custom_type_with_resource_dependent_type_check():
    def define_type_check_job(should_require_resources):
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

        @op(
            out={
                "custom_type": Out(
                    CustomType,
                )
            }
        )
        def custom_type_op(_):
            return "A"

        @job(resource_defs={"a": resource_a})
        def type_check_job():
            custom_type_op()

        return type_check_job

    under_required_job = define_type_check_job(should_require_resources=False)
    with pytest.raises(DagsterUnknownResourceError):
        under_required_job.execute_in_process()

    sufficiently_required_job = define_type_check_job(should_require_resources=True)
    assert sufficiently_required_job.execute_in_process().success


def test_resource_no_version():
    @resource
    def no_version_resource(_):
        pass

    assert no_version_resource.version is None


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

    @op(
        out={
            "custom_type": Out(
                CustomType,
            )
        }
    )
    def custom_type_op(_):
        return "A"

    with pytest.raises(DagsterInvalidDefinitionError, match="required by type 'NeedsA'"):

        @job
        def _type_check_job():
            custom_type_op()

        @repository
        def _repo():
            return [_type_check_job]


def test_loader_missing_resource_fails():
    @dagster_type_loader(String, required_resource_keys={"a"})
    def InputHydration(context, hello):
        assert context.resources.a == "A"
        return CustomType(hello)

    @usable_as_dagster_type(loader=InputHydration)
    class CustomType(str):
        pass

    @op(ins={"_custom_type": In(CustomType)})
    def custom_type_op(_, _custom_type):
        return "A"

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match="required by the loader on type 'CustomType'",
    ):

        @job
        def _type_check_job():
            custom_type_op()

        @repository
        def _repo():
            return [_type_check_job]


def test_extra_resources():
    @resource
    def resource_a(_):
        return "a"

    @resource(config_schema=int)
    def resource_b(_):
        return "b"

    @op(required_resource_keys={"A"})
    def echo(context):
        return context.resources.A

    @job(
        resource_defs={
            "A": resource_a,
            "B": resource_b,
            "BB": resource_b,
        }
    )
    def extra():
        echo()

    # should work since B & BB's resources are not needed so missing config should be fine
    assert extra.execute_in_process().success


def test_extra_configured_resources():
    @resource
    def resource_a(_):
        return "a"

    @resource(config_schema=int)
    def resource_b(_):
        return "b"

    @configured(resource_b, str)
    def resource_b2(config):
        assert False, "resource_b2 config mapping should not have been invoked"
        return int(config)

    @op(required_resource_keys={"A"})
    def echo(context):
        return context.resources.A

    @job(
        resource_defs={
            "A": resource_a,
            "B": resource_b2,
        }
    )
    def extra():
        echo()

    assert extra.execute_in_process().success


def test_root_input_manager():
    @op
    def start(_):
        return 4

    @op(ins={"x": In(root_manager_key="root_in")})
    def end(_, x):
        return x

    @job
    def _valid():
        end(start())

    with pytest.raises(DagsterInvalidSubsetError):
        _invalid = _valid.get_subset(op_selection=["wraps_b_error"])


def test_root_input_manager_missing_fails():
    @op(ins={"root_input": In(root_manager_key="missing_root_input_manager")})
    def requires_missing_root_input_manager(root_input: int):
        return root_input

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "input manager with key 'missing_root_input_manager' required by input 'root_input' of"
            " op 'requires_missing_root_input_manager' was not provided"
        ),
    ):

        @job
        def _invalid():
            requires_missing_root_input_manager()

        @repository
        def _repo():
            return [_invalid]


def test_io_manager_missing_fails():
    @op(out={"result": Out(int, io_manager_key="missing_io_manager")})
    def requires_missing_io_manager():
        return 1

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "io manager with key 'missing_io_manager' required by output 'result' of op"
            " 'requires_missing_io_manager'' was not provided"
        ),
    ):

        @job
        def _invalid():
            requires_missing_io_manager()

        @repository
        def _repo():
            return [_invalid]
