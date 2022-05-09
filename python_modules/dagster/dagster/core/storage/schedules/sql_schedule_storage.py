from abc import abstractmethod
from collections import defaultdict
from datetime import datetime
from typing import Callable, Iterable, Mapping, Optional, Sequence, cast

import pendulum
import sqlalchemy as db

import dagster._check as check
from dagster.core.definitions.run_request import InstigatorType
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.scheduler.instigation import InstigatorState, InstigatorTick, TickData, TickStatus
from dagster.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple
from dagster.utils import utc_datetime_from_timestamp

from .base import ScheduleStorage
from .migration import (
    OPTIONAL_SCHEDULE_DATA_MIGRATIONS,
    REQUIRED_SCHEDULE_DATA_MIGRATIONS,
    SCHEDULE_JOBS_SELECTOR_ID,
    SCHEDULE_TICKS_SELECTOR_ID,
)
from .schema import InstigatorsTable, JobTable, JobTickTable, SecondaryIndexMigrationTable


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

    def all_instigator_state(
        self, repository_origin_id=None, repository_selector_id=None, instigator_type=None
    ):
        check.opt_inst_param(instigator_type, "instigator_type", InstigatorType)

        if self.has_instigators_table() and self.has_built_index(SCHEDULE_JOBS_SELECTOR_ID):
            query = db.select([InstigatorsTable.c.instigator_body]).select_from(InstigatorsTable)
            if repository_selector_id:
                query = query.where(
                    InstigatorsTable.c.repository_selector_id == repository_selector_id
                )
            if instigator_type:
                query = query.where(InstigatorsTable.c.instigator_type == instigator_type.value)
        else:
            query = db.select([JobTable.c.job_body]).select_from(JobTable)
            if repository_origin_id:
                query = query.where(JobTable.c.repository_origin_id == repository_origin_id)
            if instigator_type:
                query = query.where(JobTable.c.job_type == instigator_type.value)

        rows = self.execute(query)
        return self._deserialize_rows(rows)

    def get_instigator_state(self, origin_id, selector_id):
        check.str_param(origin_id, "origin_id")
        check.str_param(selector_id, "selector_id")

        if self.has_instigators_table() and self.has_built_index(SCHEDULE_JOBS_SELECTOR_ID):
            query = (
                db.select([InstigatorsTable.c.instigator_body])
                .select_from(InstigatorsTable)
                .where(InstigatorsTable.c.selector_id == selector_id)
            )
        else:
            query = (
                db.select([JobTable.c.job_body])
                .select_from(JobTable)
                .where(JobTable.c.job_origin_id == origin_id)
            )

        rows = self.execute(query)
        return self._deserialize_rows(rows[:1])[0] if len(rows) else None

    def _has_instigator_state_by_selector(self, selector_id):
        check.str_param(selector_id, "selector_id")

        query = (
            db.select([JobTable.c.job_body])
            .select_from(JobTable)
            .where(JobTable.c.selector_id == selector_id)
        )

        rows = self.execute(query)
        return self._deserialize_rows(rows[:1])[0] if len(rows) else None

    def _add_or_update_instigators_table(self, conn, state):
        selector_id = state.selector_id
        try:
            conn.execute(
                InstigatorsTable.insert().values(  # pylint: disable=no-value-for-parameter
                    selector_id=selector_id,
                    repository_selector_id=state.repository_selector_id,
                    status=state.status.value,
                    instigator_type=state.instigator_type.value,
                    instigator_body=serialize_dagster_namedtuple(state),
                )
            )
        except db.exc.IntegrityError:
            conn.execute(
                InstigatorsTable.update()
                .where(InstigatorsTable.c.selector_id == selector_id)
                .values(
                    status=state.status.value,
                    instigator_type=state.instigator_type.value,
                    instigator_body=serialize_dagster_namedtuple(state),
                    update_timestamp=pendulum.now("UTC"),
                )
            )

    def add_instigator_state(self, state):
        check.inst_param(state, "state", InstigatorState)
        with self.connect() as conn:
            try:
                conn.execute(
                    JobTable.insert().values(  # pylint: disable=no-value-for-parameter
                        job_origin_id=state.instigator_origin_id,
                        repository_origin_id=state.repository_origin_id,
                        status=state.status.value,
                        job_type=state.instigator_type.value,
                        job_body=serialize_dagster_namedtuple(state),
                    )
                )
            except db.exc.IntegrityError as exc:
                raise DagsterInvariantViolationError(
                    f"InstigatorState {state.instigator_origin_id} is already present in storage"
                ) from exc

            # try writing to the instigators table
            if self._has_instigators_table(conn):
                self._add_or_update_instigators_table(conn, state)

        return state

    def update_instigator_state(self, state):
        check.inst_param(state, "state", InstigatorState)
        if not self.get_instigator_state(state.instigator_origin_id, state.selector_id):
            raise DagsterInvariantViolationError(
                "InstigatorState {id} is not present in storage".format(
                    id=state.instigator_origin_id
                )
            )

        values = {
            "status": state.status.value,
            "job_body": serialize_dagster_namedtuple(state),
            "update_timestamp": pendulum.now("UTC"),
        }
        if self.has_instigators_table():
            values["selector_id"] = state.selector_id

        with self.connect() as conn:
            conn.execute(
                JobTable.update()  # pylint: disable=no-value-for-parameter
                .where(JobTable.c.job_origin_id == state.instigator_origin_id)
                .values(**values)
            )
            if self._has_instigators_table(conn):
                self._add_or_update_instigators_table(conn, state)

    def delete_instigator_state(self, origin_id, selector_id):
        check.str_param(origin_id, "origin_id")
        check.str_param(selector_id, "selector_id")

        if not self.get_instigator_state(origin_id, selector_id):
            raise DagsterInvariantViolationError(
                "InstigatorState {id} is not present in storage".format(id=origin_id)
            )

        with self.connect() as conn:
            conn.execute(
                JobTable.delete().where(  # pylint: disable=no-value-for-parameter
                    JobTable.c.job_origin_id == origin_id
                )
            )

            if self._has_instigators_table(conn):
                if not self._jobs_has_selector_state(conn, selector_id):
                    conn.execute(
                        InstigatorsTable.delete().where(  # pylint: disable=no-value-for-parameter
                            InstigatorsTable.c.selector_id == selector_id
                        )
                    )

    def _jobs_has_selector_state(self, conn, selector_id):
        query = (
            db.select([db.func.count()])
            .select_from(JobTable)
            .where(JobTable.c.selector_id == selector_id)
        )
        result = conn.execute(query)
        row = result.fetchone()
        result.close()
        return row[0] > 0

    def _add_filter_limit(self, query, before=None, after=None, limit=None, statuses=None):
        check.opt_float_param(before, "before")
        check.opt_float_param(after, "after")
        check.opt_int_param(limit, "limit")
        check.opt_list_param(statuses, "statuses", of_type=TickStatus)

        if before:
            query = query.where(JobTickTable.c.timestamp < utc_datetime_from_timestamp(before))
        if after:
            query = query.where(JobTickTable.c.timestamp > utc_datetime_from_timestamp(after))
        if limit:
            query = query.limit(limit)
        if statuses:
            query = query.where(JobTickTable.c.status.in_([status.value for status in statuses]))
        return query

    @property
    def supports_batch_queries(self):
        return self.has_instigators_table() and self.has_built_index(SCHEDULE_TICKS_SELECTOR_ID)

    def has_instigators_table(self):
        with self.connect() as conn:
            return self._has_instigators_table(conn)

    def _has_instigators_table(self, conn):
        table_names = db.inspect(conn).get_table_names()
        return "instigators" in table_names

    def get_batch_ticks(
        self,
        selector_ids: Sequence[str],
        limit: Optional[int] = None,
        statuses: Optional[Sequence[TickStatus]] = None,
    ) -> Mapping[str, Iterable[InstigatorTick]]:
        check.list_param(selector_ids, "selector_ids", of_type=str)
        check.opt_int_param(limit, "limit")
        check.opt_list_param(statuses, "statuses", of_type=TickStatus)

        bucket_rank_column = (
            db.func.rank()
            .over(
                order_by=db.desc(JobTickTable.c.timestamp),
                partition_by=JobTickTable.c.selector_id,
            )
            .label("rank")
        )
        subquery = (
            db.select(
                [
                    JobTickTable.c.id,
                    JobTickTable.c.selector_id,
                    JobTickTable.c.tick_body,
                    bucket_rank_column,
                ]
            )
            .select_from(JobTickTable)
            .where(JobTickTable.c.selector_id.in_(selector_ids))
            .alias("subquery")
        )
        if statuses:
            subquery = subquery.where(
                JobTickTable.c.status.in_([status.value for status in statuses])
            )

        query = (
            db.select([subquery.c.id, subquery.c.selector_id, subquery.c.tick_body])
            .order_by(subquery.c.rank.asc())
            .where(subquery.c.rank <= limit)
        )

        rows = self.execute(query)
        results = defaultdict(list)
        for row in rows:
            tick_id = row[0]
            selector_id = row[1]
            tick_data = cast(TickData, deserialize_json_to_dagster_namedtuple(row[2]))
            results[selector_id].append(InstigatorTick(tick_id, tick_data))
        return results

    def get_ticks(self, origin_id, selector_id, before=None, after=None, limit=None, statuses=None):
        check.str_param(origin_id, "origin_id")
        check.opt_float_param(before, "before")
        check.opt_float_param(after, "after")
        check.opt_int_param(limit, "limit")
        check.opt_list_param(statuses, "statuses", of_type=TickStatus)

        base_query = (
            db.select([JobTickTable.c.id, JobTickTable.c.tick_body])
            .select_from(JobTickTable)
            .order_by(JobTickTable.c.timestamp.desc())
        )
        if self.has_instigators_table():
            query = base_query.where(
                db.or_(
                    JobTickTable.c.selector_id == selector_id,
                    db.and_(
                        JobTickTable.c.selector_id == None,
                        JobTickTable.c.job_origin_id == origin_id,
                    ),
                )
            )
        else:
            query = base_query.where(JobTickTable.c.job_origin_id == origin_id)

        query = self._add_filter_limit(
            query, before=before, after=after, limit=limit, statuses=statuses
        )

        rows = self.execute(query)
        return list(
            map(lambda r: InstigatorTick(r[0], deserialize_json_to_dagster_namedtuple(r[1])), rows)
        )

    def create_tick(self, tick_data):
        check.inst_param(tick_data, "tick_data", TickData)

        values = {
            "job_origin_id": tick_data.instigator_origin_id,
            "status": tick_data.status.value,
            "type": tick_data.instigator_type.value,
            "timestamp": utc_datetime_from_timestamp(tick_data.timestamp),
            "tick_body": serialize_dagster_namedtuple(tick_data),
        }
        if self.has_instigators_table() and tick_data.selector_id:
            values["selector_id"] = tick_data.selector_id

        with self.connect() as conn:
            try:
                tick_insert = JobTickTable.insert().values(
                    **values
                )  # pylint: disable=no-value-for-parameter
                result = conn.execute(tick_insert)
                tick_id = result.inserted_primary_key[0]
                return InstigatorTick(tick_id, tick_data)
            except db.exc.IntegrityError as exc:
                raise DagsterInvariantViolationError(
                    f"Unable to insert InstigatorTick for job {tick_data.instigator_name} in storage"
                ) from exc

    def update_tick(self, tick):
        check.inst_param(tick, "tick", InstigatorTick)

        values = {
            "status": tick.status.value,
            "type": tick.instigator_type.value,
            "timestamp": utc_datetime_from_timestamp(tick.timestamp),
            "tick_body": serialize_dagster_namedtuple(tick.tick_data),
        }
        if self.has_instigators_table() and tick.selector_id:
            values["selector_id"] = tick.selector_id

        with self.connect() as conn:
            conn.execute(
                JobTickTable.update()  # pylint: disable=no-value-for-parameter
                .where(JobTickTable.c.id == tick.tick_id)
                .values(**values)
            )

        return tick

    def purge_ticks(self, origin_id, selector_id, tick_status, before):
        check.str_param(origin_id, "origin_id")
        check.inst_param(tick_status, "tick_status", TickStatus)
        check.float_param(before, "before")

        utc_before = utc_datetime_from_timestamp(before)

        base_query = (
            JobTickTable.delete()  # pylint: disable=no-value-for-parameter
            .where(JobTickTable.c.status == tick_status.value)
            .where(JobTickTable.c.timestamp < utc_before)
        )

        if self.has_instigators_table():
            query = base_query.where(
                db.or_(
                    JobTickTable.c.selector_id == selector_id,
                    db.and_(
                        JobTickTable.c.selector_id == None,
                        JobTickTable.c.job_origin_id == origin_id,
                    ),
                )
            )
        else:
            query = base_query.where(JobTickTable.c.job_origin_id == origin_id)

        with self.connect() as conn:
            conn.execute(query)

    def wipe(self):
        """Clears the schedule storage."""
        with self.connect() as conn:
            # https://stackoverflow.com/a/54386260/324449
            conn.execute(JobTable.delete())  # pylint: disable=no-value-for-parameter
            conn.execute(JobTickTable.delete())  # pylint: disable=no-value-for-parameter
            if self._has_instigators_table(conn):
                conn.execute(InstigatorsTable.delete())

    # MIGRATIONS

    def has_secondary_index_table(self):
        with self.connect() as conn:
            return "secondary_indexes" in db.inspect(conn).get_table_names()

    def has_built_index(self, migration_name: str) -> bool:
        if not self.has_secondary_index_table():
            return False

        query = (
            db.select([1])
            .where(SecondaryIndexMigrationTable.c.name == migration_name)
            .where(SecondaryIndexMigrationTable.c.migration_completed != None)
            .limit(1)
        )
        with self.connect() as conn:
            results = conn.execute(query).fetchall()

        return len(results) > 0

    def mark_index_built(self, migration_name: str):
        query = (
            SecondaryIndexMigrationTable.insert().values(  # pylint: disable=no-value-for-parameter
                name=migration_name,
                migration_completed=datetime.now(),
            )
        )
        with self.connect() as conn:
            try:
                conn.execute(query)
            except db.exc.IntegrityError:
                conn.execute(
                    SecondaryIndexMigrationTable.update()  # pylint: disable=no-value-for-parameter
                    .where(SecondaryIndexMigrationTable.c.name == migration_name)
                    .values(migration_completed=datetime.now())
                )

    def _execute_data_migrations(
        self, migrations, print_fn: Optional[Callable] = None, force_rebuild_all: bool = False
    ):
        for migration_name, migration_fn in migrations.items():
            if self.has_built_index(migration_name):
                if not force_rebuild_all:
                    if print_fn:
                        print_fn("Skipping already applied migration: {}".format(migration_name))
                    continue
            if print_fn:
                print_fn(f"Starting data migration: {migration_name}")
            migration_fn()(self, print_fn)
            self.mark_index_built(migration_name)
            if print_fn:
                print_fn(f"Finished data migration: {migration_name}")

    def migrate(self, print_fn: Optional[Callable] = None, force_rebuild_all: bool = False):
        self._execute_data_migrations(
            REQUIRED_SCHEDULE_DATA_MIGRATIONS, print_fn, force_rebuild_all
        )

    def optimize(self, print_fn: Optional[Callable] = None, force_rebuild_all: bool = False):
        self._execute_data_migrations(
            OPTIONAL_SCHEDULE_DATA_MIGRATIONS, print_fn, force_rebuild_all
        )
