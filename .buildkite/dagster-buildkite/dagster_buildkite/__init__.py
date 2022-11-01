import logging
import os

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=os.getenv("LOGLEVEL", "INFO"),
    datefmt="%Y-%m-%d %H:%M:%S",
)
