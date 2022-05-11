from typing import List, Tuple

from dagster import DynamicOut, DynamicOutput, job, op


@op
def one():
    return 1


@op
def add(a, b):
    return a + b


@op
def echo(x):
    return x


@op
def process(results):
    return sum(results)


@op
def dynamic_values() -> List[DynamicOutput[int]]:
    outputs = []
    for i in range(2):
        outputs.append(DynamicOutput(i, mapping_key=f"num_{i}"))
    return outputs


@op(
    out={
        "values": DynamicOut(),
        "negatives": DynamicOut(),
    },
)
def multiple_dynamic_values():
    outputs = []
    for i in range(2):
        outputs.append(DynamicOutput(i, output_name="values", mapping_key=f"num_{i}"))
        outputs.append(
            DynamicOutput(-i, output_name="negatives", mapping_key=f"neg_{i}")
        )


class BigData:
    def __init__(self):
        self._data = {}

    def chunk(self):
        return self._data.items()


def load_big_data():
    return BigData()


def expensive_processing(x):
    return x


def analyze(x):
    return x


# non_dyn_start
@op
def data_processing():
    large_data = load_big_data()
    interesting_result = expensive_processing(large_data)
    return analyze(interesting_result)


@job
def naive():
    data_processing()


# non_dyn_end

# dyn_out_start
@op(out=DynamicOut())
def load_pieces():
    large_data = load_big_data()
    for idx, piece in large_data.chunk():
        yield DynamicOutput(piece, mapping_key=idx)


# dyn_out_end


@op
def compute_piece(piece):
    return expensive_processing(piece)


@op
def merge_and_analyze(results):
    return analyze(results)


# dyn_job_start
@job
def dynamic_graph():
    pieces = load_pieces()
    results = pieces.map(compute_piece)
    merge_and_analyze(results.collect())


# dyn_job_end


# dyn_chain_start
@job
def chained():
    results = dynamic_values().map(echo).map(echo).map(echo)
    process(results.collect())


@job
def chained_alt():
    def _for_each(val):
        a = echo(val)
        b = echo(a)
        return echo(b)

    results = dynamic_values().map(_for_each)
    process(results.collect())


# dyn_chain_end

# dyn_add_start
@job
def other_arg():
    non_dynamic = one()
    dynamic_values().map(lambda val: add(val, non_dynamic))


# dyn_add_end
# dyn_mult_start
@job
def multiple():
    # can unpack on assignment (order based)
    values, _ = multiple_dynamic_values()
    process(values.collect())

    # or access by name
    outs = multiple_dynamic_values()
    process(outs.values.collect())


# dyn_mult_end
