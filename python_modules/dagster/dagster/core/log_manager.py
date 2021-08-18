import datetime
import logging
from typing import TYPE_CHECKING, Any, Dict, List, NamedTuple, Optional

from dagster import check
from dagster.core.utils import coerce_valid_log_level, make_new_run_id

if TYPE_CHECKING:
    from dagster.core.events import DagsterEvent

DAGSTER_META_KEY = "dagster_meta"


class DagsterMessageProps(
    NamedTuple(
        "_DagsterMessageProps",
        [
            ("orig_message", Optional[str]),
            ("log_message_id", Optional[str]),
            ("log_timestamp", Optional[str]),
            ("dagster_event", Optional[Any]),
        ],
    )
):
    """Internal class used to represent specific attributes about a logged message"""

    def __new__(
        cls,
        orig_message: str,
        log_message_id: Optional[str] = None,
        log_timestamp: Optional[str] = None,
        dagster_event: Optional["DagsterEvent"] = None,
    ):
        return super().__new__(
            cls,
            orig_message=check.str_param(orig_message, "orig_message"),
            log_message_id=check.opt_str_param(
                log_message_id, "log_message_id", default=make_new_run_id()
            ),
            log_timestamp=check.opt_str_param(
                log_timestamp, "log_timestamp", default=datetime.datetime.utcnow().isoformat()
            ),
            dagster_event=dagster_event,
        )

    @property
    def error_str(self) -> Optional[str]:
        if self.dagster_event is None:
            return None

        event_specific_data = self.dagster_event.event_specific_data
        if not event_specific_data:
            return None

        error = getattr(event_specific_data, "error", None)
        if error:
            return "\n\n" + getattr(event_specific_data, "error_display_string", error.to_string())
        return None

    @property
    def pid(self) -> Optional[str]:
        if self.dagster_event is None or self.dagster_event.pid is None:
            return None
        return str(self.dagster_event.pid)

    @property
    def step_key(self) -> Optional[str]:
        if self.dagster_event is None:
            return None
        return self.dagster_event.step_key

    @property
    def event_type_value(self) -> Optional[str]:
        if self.dagster_event is None:
            return None
        return self.dagster_event.event_type_value


class DagsterLoggingMetadata(
    NamedTuple(
        "_DagsterLoggingMetadata",
        [
            ("run_id", Optional[str]),
            ("pipeline_name", Optional[str]),
            ("pipeline_tags", Dict[str, str]),
            ("step_key", Optional[str]),
            ("solid_name", Optional[str]),
            ("resource_name", Optional[str]),
            ("resource_fn_name", Optional[str]),
        ],
    )
):
    """Internal class used to represent the context in which a given message was logged (i.e. the
    step, pipeline run, resource, etc.)
    """

    def __new__(
        cls,
        run_id: str = None,
        pipeline_name: str = None,
        pipeline_tags: Dict[str, str] = None,
        step_key: str = None,
        solid_name: str = None,
        resource_name: str = None,
        resource_fn_name: str = None,
    ):
        return super().__new__(
            cls,
            run_id=run_id,
            pipeline_name=pipeline_name,
            pipeline_tags=pipeline_tags or {},
            step_key=step_key,
            solid_name=solid_name,
            resource_name=resource_name,
            resource_fn_name=resource_fn_name,
        )

    @property
    def log_source(self):
        if self.resource_name is None:
            return self.pipeline_name or "system"
        return f"resource:{self.resource_name}"

    def to_tags(self) -> Dict[str, str]:
        # converts all values into strings
        return {k: str(v) for k, v in self._asdict().items()}


def construct_log_string(
    logging_metadata: DagsterLoggingMetadata, message_props: DagsterMessageProps
) -> str:

    return (
        " - ".join(
            filter(
                None,
                (
                    logging_metadata.log_source,
                    logging_metadata.run_id,
                    message_props.pid,
                    logging_metadata.step_key,
                    message_props.event_type_value,
                    message_props.orig_message,
                ),
            )
        )
        + (message_props.error_str or "")
    )


class DagsterLogManager(logging.Logger):
    def __init__(
        self,
        logging_metadata: DagsterLoggingMetadata,
        loggers: List[logging.Logger],
        handlers: Optional[List[logging.Handler]] = None,
    ):
        self._logging_metadata = check.inst_param(
            logging_metadata, "logging_metadata", DagsterLoggingMetadata
        )
        self._loggers = check.list_param(loggers, "loggers", of_type=logging.Logger)

        super().__init__(name="dagster", level=logging.DEBUG)

        check.opt_nullable_list_param(handlers, "handlers", of_type=logging.Handler)
        if handlers:
            for handler in handlers:
                self.addHandler(handler)

    @property
    def logging_metadata(self) -> DagsterLoggingMetadata:
        return self._logging_metadata

    @property
    def loggers(self) -> List[logging.Logger]:
        return self._loggers

    def log_dagster_event(self, level: int, msg: str, dagster_event: "DagsterEvent"):
        self.log(level=level, msg=msg, extra={DAGSTER_META_KEY: dagster_event})

    def log(self, level, msg, *args, **kwargs):
        # allow for string level names
        super().log(coerce_valid_log_level(level), msg, *args, **kwargs)

    def _log(
        self, level, msg, args, exc_info=None, extra=None, stack_info=False
    ):  # pylint: disable=arguments-differ

        # we stash dagster meta information in the extra field
        extra = extra or {}

        dagster_message_props = DagsterMessageProps(
            orig_message=msg, dagster_event=extra.get(DAGSTER_META_KEY)
        )

        # convert the message to our preferred format
        msg = construct_log_string(self.logging_metadata, dagster_message_props)

        # combine all dagster meta information into a single dictionary
        meta_dict = {
            **self.logging_metadata._asdict(),
            **dagster_message_props._asdict(),
        }
        # step-level events can be logged from a pipeline context. for these cases, pull the step
        # key from the underlying DagsterEvent
        if meta_dict["step_key"] is None:
            meta_dict["step_key"] = dagster_message_props.step_key

        extra[DAGSTER_META_KEY] = meta_dict

        for logger in self._loggers:
            logger.log(level, msg, *args, extra=extra)

        super()._log(level, msg, args)

    def with_tags(self, **new_tags):
        """Add new tags in "new_tags" to the set of tags attached to this log manager instance, and
        return a new DagsterLogManager with the merged set of tags.

        Args:
            tags (Dict[str,str]): Dictionary of tags

        Returns:
            DagsterLogManager: a new DagsterLogManager namedtuple with updated tags for the same
                run ID and loggers.
        """
        return DagsterLogManager(
            logging_metadata=self.logging_metadata._replace(**new_tags),
            loggers=self._loggers,
            handlers=self.handlers,
        )
