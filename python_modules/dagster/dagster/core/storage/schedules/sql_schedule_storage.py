from abc import abstractmethod
from datetime import datetime

import sqlalchemy as db
from dagster import check
from dagster.core.definitions.job import JobType
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.scheduler.job import (
    JobState,
    JobTick,
    JobTickData,
    JobTickStatsSnapshot,
    JobTickStatus,
)
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.utils import utc_datetime_from_timestamp

from .base import ScheduleStorage
from .schema import JobTable, JobTickTable


class SqlScheduleStorage(ScheduleStorage):
    """Base class for SQL backed schedule storage"""

    @abstractmethod
    def connect(self):
        """Context manager yielding a sqlalchemy.engine.Connection."""

    def execute(self, query):
        with self.connect() as conn:
            result_proxy = conn.execute(query)
            res = result_proxy.fetchall()
            result_proxy.close()

        return res

    def _deserialize_rows(self, rows):
        return list(map(lambda r: deserialize_json_to_dagster_namedtuple(r[0]), rows))

    def all_stored_job_state(self, repository_origin_id=None, job_type=None):
        check.opt_inst_param(job_type, "job_type", JobType)
        base_query = db.select([JobTable.c.job_body, JobTable.c.job_origin_id]).select_from(
            JobTable
        )

        if repository_origin_id:
            query = base_query.where(JobTable.c.repository_origin_id == repository_origin_id)
        else:
            query = base_query

        if job_type:
            query = query.where(JobTable.c.job_type == job_type.value)

        rows = self.execute(query)
        return self._deserialize_rows(rows)

    def get_job_state(self, job_origin_id):
        check.str_param(job_origin_id, "job_origin_id")

        query = (
            db.select([JobTable.c.job_body])
            .select_from(JobTable)
            .where(JobTable.c.job_origin_id == job_origin_id)
        )

        rows = self.execute(query)
        return self._deserialize_rows(rows[:1])[0] if len(rows) else None

    def add_job_state(self, job):
        check.inst_param(job, "job", JobState)
        with self.connect() as conn:
            try:
                conn.execute(
                    JobTable.insert().values(  # pylint: disable=no-value-for-parameter
                        job_origin_id=job.job_origin_id,
                        repository_origin_id=job.repository_origin_id,
                        status=job.status.value,
                        job_type=job.job_type.value,
                        job_body=serialize_dagster_namedtuple(job),
                    )
                )
            except db.exc.IntegrityError as exc:
                raise DagsterInvariantViolationError(
                    f"JobState {job.job_origin_id} is already present in storage"
                ) from exc

        return job

    def update_job_state(self, job):
        check.inst_param(job, "job", JobState)
        if not self.get_job_state(job.job_origin_id):
            raise DagsterInvariantViolationError(
                "JobState {id} is not present in storage".format(id=job.job_origin_id)
            )

        with self.connect() as conn:
            conn.execute(
                JobTable.update()  # pylint: disable=no-value-for-parameter
                .where(JobTable.c.job_origin_id == job.job_origin_id)
                .values(
                    status=job.status.value,
                    job_body=serialize_dagster_namedtuple(job),
                )
            )

    def delete_job_state(self, job_origin_id):
        check.str_param(job_origin_id, "job_origin_id")

        if not self.get_job_state(job_origin_id):
            raise DagsterInvariantViolationError(
                "JobState {id} is not present in storage".format(id=job_origin_id)
            )

        with self.connect() as conn:
            conn.execute(
                JobTable.delete().where(  # pylint: disable=no-value-for-parameter
                    JobTable.c.job_origin_id == job_origin_id
                )
            )

    def get_latest_job_tick(self, job_origin_id):
        check.str_param(job_origin_id, "job_origin_id")

        query = (
            db.select([JobTickTable.c.id, JobTickTable.c.tick_body])
            .select_from(JobTickTable)
            .where(JobTickTable.c.job_origin_id == job_origin_id)
            .order_by(JobTickTable.c.timestamp.desc())
            .limit(1)
        )

        rows = self.execute(query)

        if len(rows) == 0:
            return None

        return JobTick(rows[0][0], deserialize_json_to_dagster_namedtuple(rows[0][1]))

    def _add_filter_limit(self, query, before=None, after=None, limit=None):
        check.opt_float_param(before, "before")
        check.opt_float_param(after, "after")
        check.opt_int_param(limit, "limit")

        if before:
            query = query.where(JobTickTable.c.timestamp < utc_datetime_from_timestamp(before))
        if after:
            query = query.where(JobTickTable.c.timestamp > utc_datetime_from_timestamp(after))
        if limit:
            query = query.limit(limit)
        return query

    def get_job_ticks(self, job_origin_id, before=None, after=None, limit=None):
        check.str_param(job_origin_id, "job_origin_id")
        check.opt_float_param(before, "before")
        check.opt_float_param(after, "after")
        check.opt_int_param(limit, "limit")

        query = (
            db.select([JobTickTable.c.id, JobTickTable.c.tick_body])
            .select_from(JobTickTable)
            .where(JobTickTable.c.job_origin_id == job_origin_id)
            .order_by(JobTickTable.c.id.desc())
        )

        query = self._add_filter_limit(query, before=before, after=after, limit=limit)

        rows = self.execute(query)
        return list(
            map(lambda r: JobTick(r[0], deserialize_json_to_dagster_namedtuple(r[1])), rows)
        )

    def create_job_tick(self, job_tick_data):
        check.inst_param(job_tick_data, "job_tick_data", JobTickData)

        with self.connect() as conn:
            try:
                tick_insert = (
                    JobTickTable.insert().values(  # pylint: disable=no-value-for-parameter
                        job_origin_id=job_tick_data.job_origin_id,
                        status=job_tick_data.status.value,
                        type=job_tick_data.job_type.value,
                        timestamp=utc_datetime_from_timestamp(job_tick_data.timestamp),
                        tick_body=serialize_dagster_namedtuple(job_tick_data),
                    )
                )
                result = conn.execute(tick_insert)
                tick_id = result.inserted_primary_key[0]
                return JobTick(tick_id, job_tick_data)
            except db.exc.IntegrityError as exc:
                raise DagsterInvariantViolationError(
                    f"Unable to insert JobTick for job {job_tick_data.job_name} in storage"
                ) from exc

    def update_job_tick(self, tick):
        check.inst_param(tick, "tick", JobTick)

        with self.connect() as conn:
            conn.execute(
                JobTickTable.update()  # pylint: disable=no-value-for-parameter
                .where(JobTickTable.c.id == tick.tick_id)
                .values(
                    status=tick.status.value,
                    type=tick.job_type.value,
                    timestamp=utc_datetime_from_timestamp(tick.timestamp),
                    tick_body=serialize_dagster_namedtuple(tick.job_tick_data),
                )
            )

        return tick

    def purge_job_ticks(self, job_origin_id, tick_status, before):
        check.str_param(job_origin_id, "job_origin_id")
        check.inst_param(tick_status, "tick_status", JobTickStatus)
        check.inst_param(before, "before", datetime)

        utc_before = utc_datetime_from_timestamp(before.timestamp())

        with self.connect() as conn:
            conn.execute(
                JobTickTable.delete()  # pylint: disable=no-value-for-parameter
                .where(JobTickTable.c.status == tick_status.value)
                .where(JobTickTable.c.timestamp < utc_before)
                .where(JobTickTable.c.job_origin_id == job_origin_id)
            )

    def get_job_tick_stats(self, job_origin_id):
        check.str_param(job_origin_id, "job_origin_id")

        query = (
            db.select([JobTickTable.c.status, db.func.count()])
            .select_from(JobTickTable)
            .where(JobTickTable.c.job_origin_id == job_origin_id)
            .group_by(JobTickTable.c.status)
        )

        rows = self.execute(query)

        counts = {}
        for status, count in rows:
            counts[status] = count

        return JobTickStatsSnapshot(
            ticks_started=counts.get(JobTickStatus.STARTED.value, 0),
            ticks_succeeded=counts.get(JobTickStatus.SUCCESS.value, 0),
            ticks_skipped=counts.get(JobTickStatus.SKIPPED.value, 0),
            ticks_failed=counts.get(JobTickStatus.FAILURE.value, 0),
        )

    def wipe(self):
        """Clears the schedule storage."""
        with self.connect() as conn:
            # https://stackoverflow.com/a/54386260/324449
            conn.execute(JobTable.delete())  # pylint: disable=no-value-for-parameter
            conn.execute(JobTickTable.delete())  # pylint: disable=no-value-for-parameter
