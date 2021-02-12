from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.host_representation.origin import ExternalPartitionSetOrigin
from dagster.serdes import whitelist_for_serdes
from dagster.utils.error import SerializableErrorInfo


@whitelist_for_serdes
class BulkActionStatus(Enum):
    REQUESTED = "REQUESTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@whitelist_for_serdes
class PartitionBackfill(
    namedtuple(
        "_PartitionBackfill",
        (
            "backfill_id partition_set_origin status partition_names from_failure "
            "reexecution_steps tags backfill_timestamp last_submitted_partition_name error"
        ),
    ),
):
    def __new__(
        cls,
        backfill_id,
        partition_set_origin,
        status,
        partition_names,
        from_failure,
        reexecution_steps,
        tags,
        backfill_timestamp,
        last_submitted_partition_name=None,
        error=None,
    ):
        return super(PartitionBackfill, cls).__new__(
            cls,
            check.str_param(backfill_id, "backfill_id"),
            check.inst_param(
                partition_set_origin, "partition_set_origin", ExternalPartitionSetOrigin
            ),
            check.inst_param(status, "status", BulkActionStatus),
            check.list_param(partition_names, "partition_names", of_type=str),
            check.bool_param(from_failure, "from_failure"),
            check.opt_list_param(reexecution_steps, "reexecution_steps", of_type=str),
            check.opt_dict_param(tags, "tags", key_type=str, value_type=str),
            check.float_param(backfill_timestamp, "backfill_timestamp"),
            check.opt_str_param(last_submitted_partition_name, "last_submitted_partition_name"),
            check.opt_inst_param(error, "error", SerializableErrorInfo),
        )

    def with_status(self, status):
        check.inst_param(status, "status", BulkActionStatus)
        return PartitionBackfill(
            self.backfill_id,
            self.partition_set_origin,
            status,
            self.partition_names,
            self.from_failure,
            self.reexecution_steps,
            self.tags,
            self.backfill_timestamp,
            self.last_submitted_partition_name,
            self.error,
        )

    def with_partition_checkpoint(self, last_submitted_partition_name):
        check.str_param(last_submitted_partition_name, "last_submitted_partition_name")
        return PartitionBackfill(
            self.backfill_id,
            self.partition_set_origin,
            self.status,
            self.partition_names,
            self.from_failure,
            self.reexecution_steps,
            self.tags,
            self.backfill_timestamp,
            last_submitted_partition_name,
            self.error,
        )

    def with_error(self, error):
        check.opt_inst_param(error, "error", SerializableErrorInfo)
        return PartitionBackfill(
            self.backfill_id,
            self.partition_set_origin,
            self.status,
            self.partition_names,
            self.from_failure,
            self.reexecution_steps,
            self.tags,
            self.backfill_timestamp,
            self.last_submitted_partition_name,
            error,
        )
