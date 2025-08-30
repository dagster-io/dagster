from dagster import op, job, DynamicOut, DynamicOutput, multiprocess_executor

@op(out=DynamicOut())
def split_data():
    for i in range(8):
        yield DynamicOutput(value={"chunk_id": i, "work_time": 0.5}, mapping_key=str(i))

@op
def process_chunk(chunk_data: dict) -> dict:
    import time
    time.sleep(chunk_data["work_time"])
    return {"processed": chunk_data["chunk_id"]}

@job(executor_def=multiprocess_executor)
def my_dynamic_job():
    chunks = split_data()
    chunks.map(process_chunk)

# This will be surprisingly slow!
# Expected: ~1.5 seconds (parallel)
# Reality: 15+ seconds (overhead dominates)
result = my_dynamic_job.execute_in_process()