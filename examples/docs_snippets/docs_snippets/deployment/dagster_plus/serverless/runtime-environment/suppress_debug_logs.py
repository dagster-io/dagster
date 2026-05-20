# start_suppress_debug_logs
import logging

# Instead of: logger = get_dagster_logger("your_logger_name")
logger = logging.getLogger("your_logger_name")
logger.debug("This debug message will be suppressed")
logger.info("This info message will show")
# end_suppress_debug_logs
