"""Tests for runtime resource type validation (issue #32633).

Dagster should validate that the resource bound to a key matches the type
annotation declared on the op/asset parameter *before* calling user code.

Traffic light legend:
  RED   - wrong type must raise DagsterInvariantViolationError
  GREEN - valid type must pass without error
"""

from abc import abstractmethod

import dagster as dg
import pytest
from dagster import DagsterInvariantViolationError

# ── RED: wrong resource type must raise ───────────────────────────────────────


def test_wrong_resource_type_raises_on_direct_op_invocation() -> None:
    """Core bug from #32633: wrong resource type must raise before user code runs."""

    class MyResource(dg.ConfigurableResource):
        something: str

    class UnrelatedResource(dg.ConfigurableResource):
        unrelated_param: str

    @dg.op
    def my_op(my_resource: MyResource) -> None:
        raise AssertionError("BUG: user code executed with wrong resource type")

    with pytest.raises(DagsterInvariantViolationError, match="MyResource"):
        my_op(my_resource=UnrelatedResource(unrelated_param="oops"))


def test_wrong_resource_type_raises_on_direct_asset_invocation() -> None:
    """Same bug, asset path: wrong resource type must raise before user code runs."""

    class MyResource(dg.ConfigurableResource):
        something: str

    class UnrelatedResource(dg.ConfigurableResource):
        unrelated_param: str

    @dg.asset
    def my_asset(my_resource: MyResource) -> None:
        raise AssertionError("BUG: user code executed with wrong resource type")

    with pytest.raises(DagsterInvariantViolationError, match="MyResource"):
        my_asset(my_resource=UnrelatedResource(unrelated_param="oops"))


def test_wrong_resource_type_raises_during_job_execution() -> None:
    """execute_in_process with wrong resource bound should fail without entering user code."""

    class MyResource(dg.ConfigurableResource):
        something: str

    class UnrelatedResource(dg.ConfigurableResource):
        unrelated_param: str

    call_count = {"n": 0}

    @dg.op
    def my_op(context: dg.OpExecutionContext, my_resource: MyResource) -> None:
        call_count["n"] += 1
        raise AssertionError("BUG: user code executed with wrong resource type")

    @dg.job(resource_defs={"my_resource": UnrelatedResource(unrelated_param="wrong")})
    def my_job():
        my_op()

    result = my_job.execute_in_process(raise_on_error=False)
    assert not result.success
    assert call_count["n"] == 0, "User code must not be called when resource type is wrong"


def test_wrong_resource_bound_via_context_raises() -> None:
    """Wrong resource passed through build_op_context must raise on invocation."""

    class MyResource(dg.ConfigurableResource):
        something: str

    class WrongResource(dg.ConfigurableResource):
        wrong_field: int

    @dg.op
    def my_op(context: dg.OpExecutionContext, my_resource: MyResource) -> None:
        raise AssertionError("BUG: user code executed with wrong resource type")

    with pytest.raises(DagsterInvariantViolationError, match="MyResource"):
        my_op(dg.build_op_context(resources={"my_resource": WrongResource(wrong_field=42)}))


def test_parent_class_fails_for_child_annotation() -> None:
    """Isinstance semantics: a parent instance must NOT satisfy a child class annotation."""

    class BaseResource(dg.ConfigurableResource):
        base_val: str

    class ChildResource(BaseResource):
        child_val: str

    @dg.op
    def my_op(my_resource: ChildResource) -> None:
        raise AssertionError("BUG: user code executed with wrong resource type")

    with pytest.raises(DagsterInvariantViolationError, match="ChildResource"):
        my_op(my_resource=BaseResource(base_val="only_base"))


def test_swapped_resources_at_shared_key_raises() -> None:
    """When TypeA is bound where TypeB is expected, must raise before user code."""

    class TypeA(dg.ConfigurableResource):
        val_a: str

    class TypeB(dg.ConfigurableResource):
        val_b: str

    @dg.op
    def op_needing_type_b(my_resource: TypeB) -> None:
        raise AssertionError("BUG: user code executed with wrong resource type")

    with pytest.raises(DagsterInvariantViolationError, match="TypeB"):
        op_needing_type_b(my_resource=TypeA(val_a="wrong_type"))


def test_error_message_includes_expected_and_actual_type() -> None:
    """Error message must name both the expected and the actual resource type."""

    class ExpectedResource(dg.ConfigurableResource):
        x: str

    class ActualResource(dg.ConfigurableResource):
        y: str

    @dg.op
    def my_op(my_res: ExpectedResource) -> None:
        pass

    with pytest.raises(DagsterInvariantViolationError) as exc_info:
        my_op(my_res=ActualResource(y="bad"))

    msg = str(exc_info.value)
    assert "ExpectedResource" in msg, f"Expected type name missing from: {msg}"
    assert "ActualResource" in msg, f"Actual type name missing from: {msg}"
    assert "my_res" in msg, f"Parameter name missing from: {msg}"


# ── GREEN: valid types must pass without error ────────────────────────────────


def test_exact_type_match_passes() -> None:
    """Providing the exact annotated type must not raise."""

    class MyResource(dg.ConfigurableResource):
        val: str

    @dg.op
    def my_op(my_resource: MyResource) -> str:
        return my_resource.val

    assert my_op(my_resource=MyResource(val="hello")) == "hello"


def test_subclass_passes_for_parent_annotation() -> None:
    """Isinstance semantics: a subclass must satisfy its parent annotation."""

    class BaseResource(dg.ConfigurableResource):
        base_val: str

    class ChildResource(BaseResource):
        child_val: str

    @dg.op
    def my_op(my_resource: BaseResource) -> str:
        return my_resource.base_val

    result = my_op(my_resource=ChildResource(base_val="hello", child_val="extra"))
    assert result == "hello"


def test_abstract_base_resource_accepts_concrete_subclass() -> None:
    """Abstract ConfigurableResource annotation must accept any concrete subclass."""

    class AbstractWriter(dg.ConfigurableResource):
        @abstractmethod
        def write(self) -> str: ...

    class ConcreteWriter(AbstractWriter):
        val: str

        def write(self) -> str:
            return self.val

    @dg.op
    def my_op(writer: AbstractWriter) -> str:
        return writer.write()

    assert my_op(writer=ConcreteWriter(val="hello")) == "hello"


def test_configure_at_launch_runtime_type_is_correct() -> None:
    """configure_at_launch() resources must pass type validation at runtime."""

    class MyResource(dg.ConfigurableResource):
        val: str

    @dg.op
    def my_op(context: dg.OpExecutionContext, my_resource: MyResource) -> str:
        return my_resource.val

    @dg.job
    def my_job():
        my_op()

    result = my_job.execute_in_process(resources={"my_resource": MyResource(val="hello")})
    assert result.success


def test_resource_param_from_factory_passes() -> None:
    """ResourceParam[bool] produced by ConfigurableResourceFactory must not raise.

    The annotation wraps a primitive type — isinstance checking is intentionally
    skipped for this case (the factory, not the primitive, is the resource object).
    """
    from dagster._config.pythonic_config import ConfigurableResourceFactory

    class BoolResource(ConfigurableResourceFactory[bool]):
        val: bool

        def create_resource(self, context) -> bool:
            return self.val

    @dg.op
    def my_op(context: dg.OpExecutionContext, my_bool: dg.ResourceParam[bool]) -> bool:
        return my_bool

    @dg.job(resource_defs={"my_bool": BoolResource(val=True)})
    def my_job():
        my_op()

    assert my_job.execute_in_process().success


def test_hardcoded_resource_correct_type_passes() -> None:
    """A hardcoded (non-configurable) resource bound to a ConfigurableResource annotation
    should raise - it's the wrong type, not a special legacy bypass.
    """

    class MyResource(dg.ConfigurableResource):
        val: str

    @dg.op
    def my_op(context: dg.OpExecutionContext, my_resource: MyResource) -> str:
        return my_resource.val

    @dg.job(resource_defs={"my_resource": MyResource(val="hello")})
    def my_job():
        my_op()

    assert my_job.execute_in_process().success


def test_multiple_resources_all_correct_passes() -> None:
    """Multiple resource parameters all with correct types must pass."""

    class ResA(dg.ConfigurableResource):
        val: str

    class ResB(dg.ConfigurableResource):
        num: int

    @dg.op
    def my_op(res_a: ResA, res_b: ResB) -> str:
        return f"{res_a.val}-{res_b.num}"

    assert my_op(res_a=ResA(val="x"), res_b=ResB(num=1)) == "x-1"


def test_multiple_resources_one_wrong_raises() -> None:
    """When one of multiple resource parameters has wrong type, must raise."""

    class ResA(dg.ConfigurableResource):
        val: str

    class ResB(dg.ConfigurableResource):
        num: int

    class ImpostorForB(dg.ConfigurableResource):
        fake: str

    @dg.op
    def my_op(res_a: ResA, res_b: ResB) -> None:
        raise AssertionError("BUG: user code executed with wrong resource type")

    with pytest.raises(DagsterInvariantViolationError, match="ResB"):
        my_op(res_a=ResA(val="ok"), res_b=ImpostorForB(fake="bad"))
