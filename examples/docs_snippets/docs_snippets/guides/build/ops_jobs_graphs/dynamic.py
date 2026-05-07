# ruff: isort: skip_file
import dagster as dg


@dg.op
def one():
    return 1


@dg.op
def add(a, b):
    return a + b


@dg.op
def echo(x):
    return x


@dg.op
def process(results):
    return sum(results)


@dg.op(out=dg.DynamicOut())
def dynamic_values():
    for i in range(2):
        yield dg.DynamicOutput(i, mapping_key=f"num_{i}")


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
@dg.op
def data_processing():
    large_data = load_big_data()
    interesting_result = expensive_processing(large_data)
    return analyze(interesting_result)


@dg.job
def naive():
    data_processing()


# non_dyn_end


# dyn_out_start
@dg.op(out=dg.DynamicOut())
def load_pieces():
    large_data = load_big_data()
    for idx, piece in large_data.chunk():
        yield dg.DynamicOutput(piece, mapping_key=idx)


# dyn_out_end


@dg.op
def compute_piece(piece):
    return expensive_processing(piece)


@dg.op
def merge_and_analyze(results):
    return analyze(results)


# dyn_job_start
@dg.job
def dynamic_graph():
    pieces = load_pieces()
    results = pieces.map(compute_piece)
    merge_and_analyze(results.collect())


# dyn_job_end

# dyn_job_full_example_start
import dagster as dg
import numpy as np


def load_big_data():
    # Mock a large dataset by creating a large array of numbers
    large_data = np.arange(100)

    # Define a simple chunk method to simulate chunking the data
    class LargeData:
        def __init__(self, data):
            self.data = data

        def chunk(self, chunk_size=2):
            for i in range(0, len(self.data), chunk_size):
                yield i // chunk_size, self.data[i : i + chunk_size]

    return LargeData(large_data)


@dg.op
def compute_piece(context: dg.OpExecutionContext, piece):
    context.log.info(f"Computing piece: {piece}")
    computed_piece = piece * 2
    context.log.info(f"Computed piece: {computed_piece}")
    return computed_piece


@dg.op
def merge_and_analyze(context: dg.OpExecutionContext, pieces):
    total = sum(pieces)
    context.log.info(f"Total sum of pieces: {total}")
    return total


@dg.op(out=dg.DynamicOut())
def load_pieces():
    large_data = load_big_data()
    for idx, piece in large_data.chunk():
        yield dg.DynamicOutput(piece, mapping_key=str(idx))


@dg.job
def dynamic_graph():
    pieces = load_pieces()
    results = pieces.map(compute_piece)
    merge_and_analyze(results.collect())


defs = dg.Definitions(jobs=[dynamic_graph])

# dyn_job_full_example_end


# dyn_chain_start
@dg.job
def chained():
    results = dynamic_values().map(echo).map(echo).map(echo)
    process(results.collect())


@dg.job
def chained_alt():
    def _for_each(val):
        a = echo(val)
        b = echo(a)
        return echo(b)

    results = dynamic_values().map(_for_each)
    process(results.collect())


# dyn_chain_end


# dyn_add_start
@dg.job
def other_arg():
    non_dynamic = one()
    dynamic_values().map(lambda val: add(val, non_dynamic))


# dyn_add_end
# dyn_mult_start
@dg.op(
    out={
        "values": dg.DynamicOut(),
        "negatives": dg.DynamicOut(),
    },
)
def multiple_dynamic_values():
    for i in range(2):
        yield dg.DynamicOutput(i, output_name="values", mapping_key=f"num_{i}")
        yield dg.DynamicOutput(-i, output_name="negatives", mapping_key=f"neg_{i}")


@dg.job
def multiple():
    # can unpack on assignment (order based)
    values, negatives = multiple_dynamic_values()
    process(values.collect())
    process(negatives.map(echo).collect())  # can use map or collect as usual

    # or access by name
    outs = multiple_dynamic_values()
    process(outs.values.collect())
    process(outs.negatives.map(echo).collect())


# dyn_mult_end


def get_pages():
    return [("1", "foo")]


# dyn_out_return_start
import dagster as dg


@dg.op(out=dg.DynamicOut())
def return_dynamic() -> list[dg.DynamicOutput[str]]:
    outputs = []
    for idx, page_key in get_pages():
        outputs.append(dg.DynamicOutput(page_key, mapping_key=idx))
    return outputs


# dyn_out_return_end
