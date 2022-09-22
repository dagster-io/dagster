from typing import List

from dagster import DynamicOutput, graph, op

# def test_direct():
#     # test being directly downstream of multiple dynamic outputs

#     @op
#     def dyn_nums() -> List[DynamicOutput[int]]:
#         return [
#             DynamicOutput(1, mapping_key="1"),
#             DynamicOutput(2, mapping_key="2"),
#         ]

#     @op
#     def dyn_alpha() -> List[DynamicOutput[str]]:
#         return [
#             DynamicOutput("a", mapping_key="a"),
#             DynamicOutput("b", mapping_key="b"),
#         ]

#     @op
#     def concat(n: int, a: str):
#         return f"{a}_{n}"

#     @graph
#     def zip_graph():
#         nums = dyn_nums()
#         letters = dyn_alpha()

#         # some way to zip
#         # concat[a,1], concat[b,2],

#     result = zip_graph.execute_in_process()
#     assert result.success

#     @graph
#     def product_graph():
#         nums = dyn_nums()
#         letters = dyn_alpha()

#         # some way to product
#         # concat[a,1], concat[a,2], concat[b,1], concat[b,2],

#     result = product_graph.execute_in_process()
#     assert result.success


def test_indirect():
    # test being indirectly downstream of multiple dynamic outputs

    @op
    def dyn_nums() -> List[DynamicOutput[int]]:
        return [
            DynamicOutput(1, mapping_key="n_1"),
            DynamicOutput(2, mapping_key="n_2"),
        ]

    @op
    def dyn_echo(num: int) -> List[DynamicOutput[int]]:
        return [DynamicOutput(i, mapping_key=f"e_{i}") for i in range(1, 1 + num)]

    @op
    def echo(x):
        return x

    @op
    def total(nums: List[int]) -> int:
        return sum(nums)

    @graph
    def progressive():
        # echo[n_1,e_1], echo[n_2,e_1], echo[n_2,e_2]
        total(dyn_nums().map(dyn_echo).map(echo).collect())

    result = progressive.execute_in_process()
    assert result.success
    assert result.output_for_node("total") == 4
