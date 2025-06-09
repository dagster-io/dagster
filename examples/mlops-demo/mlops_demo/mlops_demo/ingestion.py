import polars as pl
import json
import pika
import dagster as dg

group_name = "ingestion"

cleaned_readings_fn = "cleaned_readings.jsonl"
cleaned_daily_statuses_fn = "cleaned_daily_statuses.jsonl"

@dg.asset(
    description="Gets all sensor readings currently in the queue. These readings are streamed continuously from all sensors.",
    required_resource_keys={"rmqconn"},
    group_name=group_name,
    kinds={"rabbitmq"},
)
def sensor_readings(context: dg.AssetExecutionContext) -> list[str]:

    rmqconn = context.resources.rmqconn

    queue = "readings"
    channel = rmqconn.channel()
    channel.queue_declare(queue=queue)

    messages = []
    
    # Drain the queue until it's empty
    while True:
        method_frame, header_frame, body = channel.basic_get(queue=queue, auto_ack=True)
        if method_frame:
            msg = body.decode("utf-8")
            context.log.info(f"Received message: {msg}")
            messages.append(msg)
        else:
            context.log.info("No more messages in queue.")
            break

    context.add_output_metadata({
        "num_messages": len(messages)
    })

    return messages
    
@dg.asset(
    description="Gets all statuses currently in the queue. The statuses are streamed asynchronously with the readings by the end of the day.",
    required_resource_keys={"rmqconn"},
    group_name=group_name,
    kinds={"rabbitmq"}
)
def daily_machine_statuses(context: dg.AssetExecutionContext) -> list[str]:

    rmqconn = context.resources.rmqconn

    queue = "daily_statuses"
    channel = rmqconn.channel()
    channel.queue_declare(queue=queue)

    messages = []
    
    # Drain the queue until it's empty
    while True:
        method_frame, header_frame, body = channel.basic_get(queue=queue, auto_ack=True)
        if method_frame:
            msg = body.decode("utf-8")
            context.log.info(f"Received message: {msg}")
            messages.append(msg)
        else:
            context.log.info("No more messages in queue {}.")
            break

    context.add_output_metadata({
        "num_messages": len(messages)
    })

    return messages

@dg.asset(
    description="Convert readings to dataframe and clean",
    group_name=group_name,
    kinds={"polars"}
)
def cleaned_readings(context: dg.AssetExecutionContext, sensor_readings: list[str]) -> pl.DataFrame:
    data = [json.loads(row) for row in sensor_readings]
    df = pl.from_records(data)

    # Here we would be doing some cleaning...

    context.add_output_metadata({
        "num_cleaned_readings": len(df)
    })

    return df

@dg.asset(
    description="Convert statuses to dataframe and clean",
    group_name=group_name,
    kinds={"polars"}
)
def cleaned_daily_statuses(context: dg.AssetExecutionContext, daily_machine_statuses: list[str]) -> pl.DataFrame:
    data = [json.loads(row) for row in daily_machine_statuses]
    df = pl.from_records(data)

    # Here we would be doing some cleaning...

    context.add_output_metadata({
        "num_raw_statuses": len(daily_machine_statuses),
        "num_cleaned_statuses": len(df)
    })

    return df

@dg.asset(
    description="A database of historical daily statuses",
    group_name=group_name,
    kinds={"file"}
)
def historical_daily_statuses(context: dg.AssetExecutionContext, cleaned_daily_statuses: pl.DataFrame) -> int:

    context.log.info(f"len(cleaned_daily_statuses): {len(cleaned_daily_statuses)}")
    with open(cleaned_daily_statuses_fn, "a+") as f:
        cleaned_daily_statuses.write_ndjson(f)

    return len(cleaned_daily_statuses)

@dg.asset(
    description="A database of historical sensor readings",
    group_name=group_name,
    kinds={"file"}
)
def historical_readings(context: dg.AssetExecutionContext, cleaned_readings: pl.DataFrame) -> int:

    context.log.info(f"len(cleaned_readings): {len(cleaned_readings)}")
    with open(cleaned_readings_fn, "a+") as f:
        cleaned_readings.write_ndjson(f)

    return len(cleaned_readings)

get_all_readings_job = dg.define_asset_job("get_all_readings_job", selection=[sensor_readings, cleaned_readings, historical_readings])
get_all_daily_machine_statuses_job = dg.define_asset_job("get_all_daily_machine_statuses_job", selection=[daily_machine_statuses, cleaned_daily_statuses, historical_daily_statuses])

@dg.sensor(
    job=get_all_readings_job,
    minimum_interval_seconds=5,
    default_status=dg.DefaultSensorStatus.RUNNING,
    required_resource_keys={"rmqconn"}
)
def min_number_of_readings_sensor(context: dg.SensorEvaluationContext):

    rmqconn = context.resources.rmqconn

    channel = rmqconn.channel()
    queue = channel.queue_declare(queue="readings")
    message_count = queue.method.message_count

    last_message_count = int(context.cursor) if context.cursor else 0
    if  message_count <= last_message_count:
        yield dg.SkipReason(f"Another run is already emptying the queue, current message count is {message_count}")
    elif message_count < 500:
        yield dg.SkipReason(f"Minimum number of messages not reached yet (it was {message_count})")
    else:
        yield dg.RunRequest()

    context.update_cursor(str(message_count))

@dg.sensor(
    job=get_all_daily_machine_statuses_job,
    minimum_interval_seconds=5,
    default_status=dg.DefaultSensorStatus.RUNNING,
    required_resource_keys={"rmqconn"}
)
def min_number_of_machine_statuses_sensor(context: dg.SensorEvaluationContext):

    rmqconn = context.resources.rmqconn

    channel = rmqconn.channel()
    queue = channel.queue_declare(queue="daily_statuses")
    message_count = queue.method.message_count

    last_message_count = int(context.cursor) if context.cursor else 0
    if  message_count <= last_message_count:
        yield dg.SkipReason(f"Another run is already emptying the queue, current message count is {message_count}")
    elif message_count < 500:
        yield dg.SkipReason(f"Minimum number of messages not reached yet (it was {message_count})")
    else:
        yield dg.RunRequest()

    context.update_cursor(str(message_count))

