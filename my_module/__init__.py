import os
import sys

# Add the parent directory to Python path to find loguru_bridge
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from loguru_bridge import dagster_context_sink, loguru_enabled

from loguru import logger
import logging
import dagster as dg

# Print configuration info (using environment variables now)
print("Loguru configuration:")
print(f"  Enabled: {os.getenv('DAGSTER_LOGURU_ENABLED', 'true')}")
print(f"  Log level: {os.getenv('DAGSTER_LOGURU_LOG_LEVEL', 'DEBUG')}")
print(f"  To file: {os.getenv('DAGSTER_LOGURU_TO_FILE', 'true')}")
print(f"  File path: {os.getenv('DAGSTER_LOGURU_FILE_PATH', '/tmp/dagster_loguru_output.log')}")


@dg.asset
def my_logger(context: dg.AssetExecutionContext) -> None:
    logger.add(dagster_context_sink(context), level="DEBUG", format="{message}")
    context.log.info("This is an info log via Dagster")

    logger.debug("This is a DEBUG from loguru")
    logger.info("This is an INFO from loguru_bridge.py")
    logger.warning("This is a WARNING from loguru")
    logger.error("This is an ERROR from loguru")
    logger.success("This is a SUCCESS from loguru")

@dg.asset
def my_asset(context: dg.AssetExecutionContext):
    logger.add(dagster_context_sink(context), level="DEBUG", format="{message}")
    logger.debug("my_asset starting execution.")
    logger.info("Hello TEAM_TURTLES!")
    logger.debug("my_asset finished execution.")

@dg.asset
def calculate_sum(context: dg.AssetExecutionContext):
    logger.add(dagster_context_sink(context), level="DEBUG", format="{message}")
    a, b = 3, 7
    logger.debug(f"Adding {a} + {b}")
    result = a + b
    logger.success(f"Result is {result}")
    return result

@dg.asset
def greet(context: dg.AssetExecutionContext):
    logger.add(dagster_context_sink(context), level="DEBUG", format="{message}")
    logger.debug("Preparing greeting message.")
    message = "Greetings from Dagster!"
    logger.info(message)
    return message

@dg.asset
def my_test_asset(context: dg.AssetExecutionContext):
    if loguru_enabled():
        logger.add(dagster_context_sink(context), level="DEBUG", format="{message}")
        context.log.info("This is an info log message")
        logger.warning("This Logger ===LOGURU=== is a warning log message")
        context.log.error("This is an error log message")
        logger.debug("my_test_asset completed without fatal issues.")

# Dagster Definitions
defs = dg.Definitions(
    assets=[my_logger, my_asset, calculate_sum, greet, my_test_asset]
)
