import dagster as dg


@dg.op
def load_large_dataset(context: dg.OpExecutionContext):
    context.log.info("Loading 10GB dataset...")
    # Your business logic here (pandas, spark, etc.)
    return {"records": 1000000}


@dg.op
def train_model(context: dg.OpExecutionContext, dataset: dict):
    context.log.info("Training model...")
    # Your business logic here (sklearn, pytorch, etc.)
    return {"model_id": "model-123", "accuracy": 0.95}


@dg.job
def ml_training_job():
    dataset = load_large_dataset()
    train_model(dataset)


@dg.op(config_schema={"query": str})
def run_complex_query(context: dg.OpExecutionContext):
    query = context.op_config["query"]
    context.log.info(f"Running long query: {query}")
    # Your business logic here (runs > 15 minutes)
    return {"rows": 1000000}


@dg.job
def long_running_job():
    run_complex_query()


@dg.op
def process_data(context: dg.OpExecutionContext):
    context.log.info("Processing large dataset...")
    # Your business logic here
    return {"processed": 1000000}


@dg.job
def process_data_job():
    process_data()
