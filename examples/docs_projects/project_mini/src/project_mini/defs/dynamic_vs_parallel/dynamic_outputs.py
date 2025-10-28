import time

import dagster as dg


@dg.op(out=dg.DynamicOut())
def load_pieces(context: dg.OpExecutionContext):
    pieces_to_process = [chr(i) for i in range(ord("a"), ord("z") + 1)]  # list a-z
    context.log.info(f"Will process... {pieces_to_process}")

    # creates an output per letter, chunking is also possible
    for piece in pieces_to_process:
        yield dg.DynamicOutput(piece, mapping_key=piece)


@dg.op
def compute_piece(piece_to_compute: str):
    time.sleep(1)
    return piece_to_compute.upper()


@dg.op
def merge_and_analyze(context: dg.OpExecutionContext, computed_pieces: list[str]):
    context.log.info(f"Finished processing, result is ... {computed_pieces}")
    return


@dg.job
def dynamic_graph():
    pieces = load_pieces()
    results = pieces.map(compute_piece)
    merge_and_analyze(results.collect())


defs = dg.Definitions(jobs=[dynamic_graph])
