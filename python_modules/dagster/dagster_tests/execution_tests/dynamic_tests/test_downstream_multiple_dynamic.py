from dagster import op, job, DynamicOut, DynamicOutput

@op(
    out=DynamicOut()
)
def base_upstream(context):
    for i in range(5):
        context.log.info(f"base upstream yielding {i}")
        yield DynamicOutput(i, mapping_key=f"base_{i}")

@op(
    out=DynamicOut()
)
def multiplier_upstream(context):
    for i in range(5):
        context.log.info(f"multiplier upstream yielding {i}")
        yield DynamicOutput(i, mapping_key=f"multiply_by_{i}")

@op
def upstream_combiner(context, base, multiplier):
    # multiplier = 5
    context.log.info(f"upstream combiner combining {base} and {multiplier}")
    return base * multiplier

@op
def collector(context, inputs):
    context.log.info(f"collector got inputs {inputs}")

@job
def multiple_upstream_dynamic():
    bases = base_upstream()
    multipliers = multiplier_upstream()
    bases.map(upstream_combiner, zip_with=multipliers)

def test_multiple_upstream():
    result = multiple_upstream_dynamic.execute_in_process()
    assert list(result.output_for_node("upstream_combiner").values()) == [0, 1, 4, 9, 16]

