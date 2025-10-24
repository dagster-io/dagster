import multiprocessing
import time

import dagster as dg


@dg.op
def load_and_process_pieces(context: dg.OpExecutionContext):
    pieces_to_process = [chr(i) for i in range(ord("a"), ord("z") + 1)]  # list a-z
    context.log.info(f"Will process... {pieces_to_process}")

    num_processes = multiprocessing.cpu_count() - 1
    pool = multiprocessing.Pool(processes=num_processes)

    computed_pieces = pool.map(compute_piece, pieces_to_process)
    pool.close()
    pool.join()

    return computed_pieces


def compute_piece(piece_to_compute: str):
    time.sleep(1)
    return piece_to_compute.upper()


@dg.op
def merge_and_analyze(context: dg.OpExecutionContext, computed_pieces: list[str]):
    context.log.info(f"Finished processing, result is ... {computed_pieces}")
    return


@dg.job
def python_parallelism():
    merge_and_analyze(load_and_process_pieces())


defs = dg.Definitions(jobs=[python_parallelism])
