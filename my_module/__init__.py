import os
import sys
import dagster as dg
import logging 

# Add the parent directory to Python path to find loguru_bridge
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import after path modification
from loguru import logger
from loguru_bridge import dagster_context_sink, loguru_enabled


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

@dg.asset
def classic_logger_test(context: dg.AssetExecutionContext):
    logger.add(dagster_context_sink(context), level="DEBUG", format="{message}")

    py_logger = logging.getLogger("classic_logger")
    py_logger.setLevel(logging.DEBUG)

    # Dagster context.log zaten bridge'li olduğu için görünür olur
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    py_logger.addHandler(handler)

    py_logger.debug("DEBUG log from classic Python logger")
    py_logger.info("INFO log from classic Python logger")
    py_logger.warning("WARNING log from classic Python logger")
    py_logger.error("ERROR log from classic Python logger")
    py_logger.critical("CRITICAL log from classic Python logger")

    context.log.info("Finished classic_logger_test")

# Dagster Definitions
defs = dg.Definitions(
    assets=[my_logger, my_asset, calculate_sum, greet, my_test_asset, classic_logger_test]
)
