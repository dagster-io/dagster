import logging

import dagster._check as check
import graphene


class GrapheneLogLevel(graphene.Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    INFO = "INFO"
    WARNING = "WARNING"
    DEBUG = "DEBUG"

    class Meta:
        name = "LogLevel"

    @classmethod
    def from_level(cls, level):
        check.int_param(level, "level")
        if level == logging.CRITICAL:
            return GrapheneLogLevel.CRITICAL
        elif level == logging.ERROR:
            return GrapheneLogLevel.ERROR
        elif level == logging.INFO:
            return GrapheneLogLevel.INFO
        elif level == logging.WARNING:
            return GrapheneLogLevel.WARNING
        elif level == logging.DEBUG:
            return GrapheneLogLevel.DEBUG
        else:
            check.failed("Invalid log level: {level}".format(level=level))
