import dagster as dg
import pytest
from dagster import ResourceDefinition


def get_resource_init_job(resources_initted: dict[str, bool]) -> dg.JobDefinition:
    @dg.resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @dg.resource
    def resource_b(_):
        resources_initted["b"] = True
        yield "B"

    @dg.op(required_resource_keys={"a"})
    def consumes_resource_a(context):
        assert context.resources.a == "A"

    @dg.op(required_resource_keys={"b"})
    def consumes_resource_b(context):
        assert context.resources.b == "B"

    @dg.job(
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
    @dg.op(required_resource_keys={"a"})
    def requires_resource_a(context):
        assert context.resources.a
        assert not hasattr(context.resources, "b")

    @dg.op(required_resource_keys={"b"})
    def requires_resource_b(context):
        assert not hasattr(context.resources, "a")
        assert context.resources.b

    @dg.op
    def not_resources(context):
        assert not hasattr(context.resources, "a")
        assert not hasattr(context.resources, "b")

    @dg.job(
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

    @dg.resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @dg.resource
    def resource_b(_):
        resources_initted["b"] = True
        yield "B"

    @dg.op(required_resource_keys={"a"})
    def consumes_resource_a(context):
        assert context.resources.a == "A"

    @dg.job(resource_defs={"a": resource_a, "b": resource_b})
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

    @dg.resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @dg.resource
    def resource_b(_):
        resources_initted["b"] = True
        yield "B"

    @dg.op(required_resource_keys={"a"})
    def consumes_resource_a(context):
        assert context.resources.a == "A"

    @dg.op(required_resource_keys={"b"})
    def consumes_resource_b(context):
        assert context.resources.b == "B"

    @dg.job(
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


def create_nested_graph_job(resources_initted: dict[str, bool]) -> dg.JobDefinition:
    @dg.resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @dg.resource
    def resource_b(_):
        resources_initted["b"] = True
        yield "B"

    @dg.op(required_resource_keys={"a"})
    def consumes_resource_a(context):
        assert context.resources.a == "A"

    @dg.op(required_resource_keys={"b"})
    def consumes_resource_b(context):
        assert context.resources.b == "B"

    @dg.op
    def consumes_resource_b_error(context):
        assert context.resources.b == "B"

    @dg.graph
    def wraps_a():
        consumes_resource_a()

    @dg.graph
    def wraps_b():
        consumes_resource_b()

    @dg.graph
    def wraps_b_error():
        consumes_resource_b()
        consumes_resource_b_error()

    @dg.job(
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

    with pytest.raises(dg.DagsterUnknownResourceError):
        create_nested_graph_job(resources_initted).execute_in_process(
            op_selection=["wraps_b_error"]
        )


def test_execution_plan_subset_with_aliases():
    resources_initted = {}

    @dg.resource
    def resource_a(_):
        resources_initted["a"] = True
        yield "A"

    @dg.resource
    def resource_b(_):
        resources_initted["b"] = True
        yield "B"

    @dg.op(required_resource_keys={"a"})
    def consumes_resource_a(context):
        assert context.resources.a == "A"

    @dg.op(required_resource_keys={"b"})
    def consumes_resource_b(context):
        assert context.resources.b == "B"

    @dg.job(
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
        @dg.resource
        def resource_a(_):
            yield "A"

        @dg.dagster_type_loader(
            dg.String, required_resource_keys={"a"} if should_require_resources else set()
        )
        def InputHydration(context, hello):
            assert context.resources.a == "A"
            return CustomType(hello)

        @dg.usable_as_dagster_type(loader=InputHydration)
        class CustomType(str):
            pass

        @dg.op(ins={"custom_type": dg.In(CustomType)})
        def input_hydration_op(context, custom_type):
            context.log.info(custom_type)

        @dg.job(resource_defs={"a": resource_a})
        def input_hydration_job():
            input_hydration_op()

        return input_hydration_job

    under_required_job = define_input_hydration_job(should_require_resources=False)
    with pytest.raises(dg.DagsterUnknownResourceError):
        under_required_job.execute_in_process(
            {"ops": {"input_hydration_op": {"inputs": {"custom_type": "hello"}}}},
        )

    sufficiently_required_job = define_input_hydration_job(should_require_resources=True)
    assert sufficiently_required_job.execute_in_process(
        {"ops": {"input_hydration_op": {"inputs": {"custom_type": "hello"}}}},
    ).success


def test_resource_dependent_hydration_with_selective_init():
    def get_resource_init_input_hydration_job(resources_initted):
        @dg.resource
        def resource_a(_):
            resources_initted["a"] = True
            yield "A"

        @dg.dagster_type_loader(dg.String, required_resource_keys={"a"})
        def InputHydration(context, hello):
            assert context.resources.a == "A"
            return CustomType(hello)

        @dg.usable_as_dagster_type(loader=InputHydration)
        class CustomType(str):
            pass

        @dg.op(ins={"custom_type": dg.In(CustomType)})
        def input_hydration_op(context, custom_type):
            context.log.info(custom_type)

        @dg.op(out=dg.Out(CustomType))
        def source_custom_type(_):
            return CustomType("from solid")

        @dg.job(resource_defs={"a": resource_a})
        def selective_job():
            input_hydration_op(source_custom_type())

        return selective_job

    resources_initted = {}
    assert get_resource_init_input_hydration_job(resources_initted).execute_in_process().success
    assert set(resources_initted.keys()) == set()


def test_custom_type_with_resource_dependent_type_check():
    def define_type_check_job(should_require_resources):
        @dg.resource
        def resource_a(_):
            yield "A"

        def resource_based_type_check(context, value):
            return context.resources.a == value

        CustomType = dg.DagsterType(
            name="NeedsA",
            type_check_fn=resource_based_type_check,
            required_resource_keys={"a"} if should_require_resources else None,
        )

        @dg.op(
            out={
                "custom_type": dg.Out(
                    CustomType,
                )
            }
        )
        def custom_type_op(_):
            return "A"

        @dg.job(resource_defs={"a": resource_a})
        def type_check_job():
            custom_type_op()

        return type_check_job

    under_required_job = define_type_check_job(should_require_resources=False)
    with pytest.raises(dg.DagsterUnknownResourceError):
        under_required_job.execute_in_process()

    sufficiently_required_job = define_type_check_job(should_require_resources=True)
    assert sufficiently_required_job.execute_in_process().success


def test_resource_no_version():
    @dg.resource
    def no_version_resource(_):
        pass

    assert no_version_resource.version is None


def test_resource_passed_version():
    @dg.resource(version="42")
    def passed_version_resource(_):
        pass

    assert passed_version_resource.version == "42"


def test_type_missing_resource_fails():
    def resource_based_type_check(context, value):
        return context.resources.a == value

    CustomType = dg.DagsterType(
        name="NeedsA",
        type_check_fn=resource_based_type_check,
        required_resource_keys={"a"},
    )

    @dg.op(
        out={
            "custom_type": dg.Out(
                CustomType,
            )
        }
    )
    def custom_type_op(_):
        return "A"

    with pytest.raises(dg.DagsterInvalidDefinitionError, match="required by type 'NeedsA'"):

        @dg.job
        def _type_check_job():
            custom_type_op()

        @dg.repository
        def _repo():
            return [_type_check_job]


def test_loader_missing_resource_fails():
    @dg.dagster_type_loader(dg.String, required_resource_keys={"a"})
    def InputHydration(context, hello):
        assert context.resources.a == "A"
        return CustomType(hello)

    @dg.usable_as_dagster_type(loader=InputHydration)
    class CustomType(str):
        pass

    @dg.op(ins={"_custom_type": dg.In(CustomType)})
    def custom_type_op(_, _custom_type):
        return "A"

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match="required by the loader on type 'CustomType'",
    ):

        @dg.job
        def _type_check_job():
            custom_type_op()

        @dg.repository
        def _repo():
            return [_type_check_job]


def test_extra_resources():
    @dg.resource
    def resource_a(_):
        return "a"

    @dg.resource(config_schema=int)
    def resource_b(_):
        return "b"

    @dg.op(required_resource_keys={"A"})
    def echo(context):
        return context.resources.A

    @dg.job(
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
    @dg.resource
    def resource_a(_):
        return "a"

    @dg.resource(config_schema=int)
    def resource_b(_):
        return "b"

    @dg.configured(resource_b, str)
    def resource_b2(config):
        assert False, "resource_b2 config mapping should not have been invoked"
        return int(config)

    @dg.op(required_resource_keys={"A"})
    def echo(context):
        return context.resources.A

    @dg.job(
        resource_defs={
            "A": resource_a,
            "B": resource_b2,
        }
    )
    def extra():
        echo()

    assert extra.execute_in_process().success


def test_input_manager():
    @dg.op
    def start(_):
        return 4

    @dg.op(ins={"x": dg.In(input_manager_key="root_in")})
    def end(_, x):
        return x

    @dg.job
    def _valid():
        end(start())

    with pytest.raises(dg.DagsterInvalidSubsetError):
        _invalid = _valid.get_subset(op_selection=["wraps_b_error"])


def test_input_manager_missing_fails():
    @dg.op(ins={"root_input": dg.In(input_manager_key="missing_input_manager")})
    def requires_missing_input_manager(root_input: int):
        return root_input

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "input manager with key 'missing_input_manager' required by input 'root_input' of"
            " op 'requires_missing_input_manager' was not provided"
        ),
    ):

        @dg.job
        def _invalid():
            requires_missing_input_manager()

        @dg.repository
        def _repo():
            return [_invalid]


def test_io_manager_missing_fails():
    @dg.op(out={"result": dg.Out(int, io_manager_key="missing_io_manager")})
    def requires_missing_io_manager():
        return 1

    with pytest.raises(
        dg.DagsterInvalidDefinitionError,
        match=(
            "io manager with key 'missing_io_manager' required by output 'result' of op"
            " 'requires_missing_io_manager'' was not provided"
        ),
    ):

        @dg.job
        def _invalid():
            requires_missing_io_manager()

        @dg.repository
        def _repo():
            return [_invalid]
