from typing import Tuple

from dagster import In, MultiOut, Nothing, Out, Output, execute_pipeline, graph, op


def execute_op_in_job(an_op):
    @graph
    def my_graph():
        an_op()

    result = execute_pipeline(my_graph.to_job())
    assert result.success
    return result


def test_op():
    @op
    def my_op():
        pass

    execute_op_in_job(my_op)


def test_ins():
    @op
    def upstream1():
        return 5

    @op
    def upstream2():
        return "6"

    @op(ins={"a": In(metadata={"x": 1}), "b": In(metadata={"y": 2})})
    def my_op(a: int, b: str) -> int:
        return a + int(b)

    @graph
    def my_graph():
        my_op(a=upstream1(), b=upstream2())

    result = execute_pipeline(my_graph.to_job())
    assert result.success

    assert upstream1() == 5

    assert upstream2() == "6"

    assert my_op(1, "2") == 3


def test_out():
    @op(out=Out(metadata={"x": 1}))
    def my_op() -> int:
        return 1

    assert my_op.output_defs[0].metadata == {"x": 1}
    assert my_op.output_defs[0].name == "result"
    assert my_op() == 1


def test_multi_out():
    @op(out=MultiOut({"a": Out(metadata={"x": 1}), "b": Out(metadata={"y": 2})}))
    def my_op() -> Tuple[int, str]:
        return 1, "q"

    assert len(my_op.output_defs) == 2

    assert my_op.output_defs[0].metadata == {"x": 1}
    assert my_op.output_defs[0].name == "a"
    assert my_op.output_defs[1].metadata == {"y": 2}
    assert my_op.output_defs[1].name == "b"

    assert my_op() == (1, "q")


def test_tuple_out():
    @op
    def my_op() -> Tuple[int, str]:
        return 1, "a"

    assert len(my_op.output_defs) == 1
    result = execute_op_in_job(my_op)
    assert result.output_for_solid("my_op") == (1, "a")

    assert my_op() == (1, "a")


def test_multi_out_yields():
    @op(out=MultiOut({"a": Out(metadata={"x": 1}), "b": Out(metadata={"y": 2})}))
    def my_op():
        yield Output(output_name="a", value=1)
        yield Output(output_name="b", value=2)

    assert my_op.output_defs[0].metadata == {"x": 1}
    assert my_op.output_defs[0].name == "a"
    assert my_op.output_defs[1].metadata == {"y": 2}
    assert my_op.output_defs[1].name == "b"
    result = execute_op_in_job(my_op)
    assert result.output_for_solid("my_op", "a") == 1
    assert result.output_for_solid("my_op", "b") == 2

    assert [output.value for output in my_op()] == [1, 2]


def test_multi_out_optional():
    @op(out=MultiOut({"a": Out(metadata={"x": 1}, is_required=False), "b": Out(metadata={"y": 2})}))
    def my_op():
        yield Output(output_name="b", value=2)

    result = execute_op_in_job(my_op)
    assert result.output_for_solid("my_op", "b") == 2

    assert [output.value for output in my_op()] == [2]


def test_ins_dict():
    @op
    def upstream1():
        return 5

    @op
    def upstream2():
        return "6"

    @op(
        ins={
            "a": In(metadata={"x": 1}),
            "b": In(metadata={"y": 2}),
        }
    )
    def my_op(a: int, b: str) -> int:
        return a + int(b)

    assert my_op.input_defs[0].dagster_type.typing_type == int
    assert my_op.input_defs[1].dagster_type.typing_type == str

    @graph
    def my_graph():
        my_op(a=upstream1(), b=upstream2())

    result = execute_pipeline(my_graph.to_job())
    assert result.success

    assert my_op(a=1, b="2") == 3


def test_multi_out_dict():
    @op(out=MultiOut({"a": Out(metadata={"x": 1}), "b": Out(metadata={"y": 2})}))
    def my_op() -> Tuple[int, str]:
        return 1, "q"

    assert len(my_op.output_defs) == 2

    assert my_op.output_defs[0].metadata == {"x": 1}
    assert my_op.output_defs[0].name == "a"
    assert my_op.output_defs[0].dagster_type.typing_type == int
    assert my_op.output_defs[1].metadata == {"y": 2}
    assert my_op.output_defs[1].name == "b"
    assert my_op.output_defs[1].dagster_type.typing_type == str

    result = execute_op_in_job(my_op)
    assert result.output_for_solid("my_op", "a") == 1
    assert result.output_for_solid("my_op", "b") == "q"

    assert my_op() == (1, "q")


def test_nothing_in():
    @op(out=Out(dagster_type=Nothing))
    def noop():
        pass

    @op(ins={"after": In(dagster_type=Nothing)})
    def on_complete():
        return "cool"

    @graph
    def nothing_test():
        on_complete(noop())

    result = execute_pipeline(nothing_test.to_job())
    assert result.success
