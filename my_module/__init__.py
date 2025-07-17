import os
import sys
import dagster as dg
from loguru import logger

# Add the parent directory to Python path to find loguru_bridge
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import custom bridge tools
from loguru_bridge import dagster_context_sink, with_loguru_logger

# Log configuration info at module load
print("Loguru configuration:")
print(f"  Enabled: {os.getenv('DAGSTER_LOGURU_ENABLED', 'true')}")
print(f"  Log level: {os.getenv('DAGSTER_LOGURU_LOG_LEVEL', 'DEBUG')}")
print(f"  To file: {os.getenv('DAGSTER_LOGURU_TO_FILE', 'true')}")
print(f"  File path: {os.getenv('DAGSTER_LOGURU_FILE_PATH', '/tmp/dagster_loguru_output.log')}")


@dg.asset
@with_loguru_logger
def my_logger(context: dg.AssetExecutionContext) -> None:
    logger.debug("This is a DEBUG from loguru")
    logger.info("This is an INFO from loguru_bridge.py")
    logger.warning("This is a WARNING from loguru")
    logger.error("This is an ERROR from loguru")
    logger.success("This is a SUCCESS from loguru")


@dg.asset
@with_loguru_logger
def my_asset(context: dg.AssetExecutionContext):
    logger.info("Hello TEAM_TURTLES!")


@dg.asset
@with_loguru_logger
def calculate_sum(context: dg.AssetExecutionContext):
    a, b = 3, 7
    logger.debug(f"Adding {a} + {b}")
    result = a + b
    logger.success(f"Result is {result}")
    return result


@dg.asset
@with_loguru_logger
def greet(context: dg.AssetExecutionContext):
    logger.debug("Preparing greeting message.")
    logger.info("Greetings from Dagster!")
    return "Greetings from Dagster!"


@dg.asset
@with_loguru_logger
def my_test_asset(context: dg.AssetExecutionContext):
    logger.warning("This is a warning log message")
    logger.error("This is an error log message")
    logger.debug("my_test_asset completed without fatal issues.")


@dg.asset
@with_loguru_logger
def classic_logger_test(context: dg.AssetExecutionContext):
    import logging
    py_logger = logging.getLogger("classic_logger")
    py_logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    py_logger.addHandler(handler)

    py_logger.debug("DEBUG from classic logger")
    py_logger.info("INFO from classic logger")
    py_logger.warning("WARNING from classic logger")
    py_logger.error("ERROR from classic logger")
    py_logger.critical("CRITICAL from classic logger")

    logger.info("Finished classic_logger_test")


# Dagster Definitions
defs = dg.Definitions(
    assets=[
        my_logger,
        my_asset,
        calculate_sum,
        greet,
        my_test_asset,
        classic_logger_test
    ]
)
