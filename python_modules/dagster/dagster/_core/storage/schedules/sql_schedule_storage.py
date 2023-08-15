from abc import abstractmethod
from collections import defaultdict
from datetime import datetime
from typing import (
    Any,
    Callable,
    ContextManager,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Type,
    TypeVar,
)

import pendulum
import sqlalchemy as db
import sqlalchemy.exc as db_exc
from sqlalchemy.engine import Connection

import dagster._check as check
from dagster._core.definitions.auto_materialize_condition import AutoMaterializeAssetEvaluation
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.run_request import InstigatorType
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.scheduler.instigation import (
    AutoMaterializeAssetEvaluationRecord,
    InstigatorState,
    InstigatorStatus,
    InstigatorTick,
    TickData,
    TickStatus,
)
from dagster._core.storage.sql import SqlAlchemyQuery, SqlAlchemyRow
from dagster._core.storage.sqlalchemy_compat import db_fetch_mappings, db_select, db_subquery
from dagster._serdes import serialize_value
from dagster._serdes.serdes import deserialize_value
from dagster._utils import PrintFn, utc_datetime_from_timestamp

from .base import ScheduleStorage
from .migration import (
    OPTIONAL_SCHEDULE_DATA_MIGRATIONS,
    REQUIRED_SCHEDULE_DATA_MIGRATIONS,
    SCHEDULE_JOBS_SELECTOR_ID,
    SCHEDULE_TICKS_SELECTOR_ID,
)
from .schema import (
    AssetDaemonAssetEvaluationsTable,
    InstigatorsTable,
    JobTable,
    JobTickTable,
    SecondaryIndexMigrationTable,
)

T_NamedTuple = TypeVar("T_NamedTuple", bound=NamedTuple)


class SqlScheduleStorage(ScheduleStorage):
    """Base class for SQL backed schedule storage."""

    @abstractmethod
    def connect(self) -> ContextManager[Connection]:
        """Context manager yielding a sqlalchemy.engine.Connection."""

    def execute(self, query: SqlAlchemyQuery) -> Sequence[SqlAlchemyRow]:
        with self.connect() as conn:
            result_proxy = conn.execute(query)
            res = result_proxy.fetchall()
            result_proxy.close()

        return res

    def _deserialize_rows(
        self, rows: Sequence[SqlAlchemyRow], as_type: Type[T_NamedTuple]
    ) -> Sequence[T_NamedTuple]:
        return list(map(lambda r: deserialize_value(r[0], as_type), rows))

    def all_instigator_state(
        self,
        repository_origin_id: Optional[str] = None,
        repository_selector_id: Optional[str] = None,
        instigator_type: Optional[InstigatorType] = None,
        instigator_statuses: Optional[Set[InstigatorStatus]] = None,
    ) -> Sequence[InstigatorState]:
        check.opt_inst_param(instigator_type, "instigator_type", InstigatorType)

        if self.has_instigators_table() and self.has_built_index(SCHEDULE_JOBS_SELECTOR_ID):
            query = db_select([InstigatorsTable.c.instigator_body]).select_from(InstigatorsTable)
            if repository_selector_id:
                query = query.where(
                    InstigatorsTable.c.repository_selector_id == repository_selector_id
                )
            if instigator_type:
                query = query.where(InstigatorsTable.c.instigator_type == instigator_type.value)
            if instigator_statuses:
                query = query.where(
                    InstigatorsTable.c.status.in_([status.value for status in instigator_statuses])
                )

        else:
            query = db_select([JobTable.c.job_body]).select_from(JobTable)
            if repository_origin_id:
                query = query.where(JobTable.c.repository_origin_id == repository_origin_id)
            if instigator_type:
                query = query.where(JobTable.c.job_type == instigator_type.value)
            if instigator_statuses:
                query = query.where(
                    JobTable.c.status.in_([status.value for status in instigator_statuses])
                )

        rows = self.execute(query)
        return self._deserialize_rows(rows, InstigatorState)

    def get_instigator_state(self, origin_id: str, selector_id: str) -> Optional[InstigatorState]:
        check.str_param(origin_id, "origin_id")
        check.str_param(selector_id, "selector_id")

        if self.has_instigators_table() and self.has_built_index(SCHEDULE_JOBS_SELECTOR_ID):
            query = (
                db_select([InstigatorsTable.c.instigator_body])
                .select_from(InstigatorsTable)
                .where(InstigatorsTable.c.selector_id == selector_id)
            )
        else:
            query = (
                db_select([JobTable.c.job_body])
                .select_from(JobTable)
                .where(JobTable.c.job_origin_id == origin_id)
            )

        rows = self.execute(query)
        return self._deserialize_rows(rows[:1], InstigatorState)[0] if len(rows) else None

    def _has_instigator_state_by_selector(self, selector_id: str) -> bool:
        check.str_param(selector_id, "selector_id")

        query = (
            db_select([JobTable.c.job_body])
            .select_from(JobTable)
            .where(JobTable.c.selector_id == selector_id)
        )

        rows = self.execute(query)
        return self._deserialize_rows(rows[:1])[0] if len(rows) else None  # type: ignore

    def _add_or_update_instigators_table(self, conn: Connection, state: InstigatorState) -> None:
        selector_id = state.selector_id
        try:
            conn.execute(
                InstigatorsTable.insert().values(
                    selector_id=selector_id,
                    repository_selector_id=state.repository_selector_id,
                    status=state.status.value,
                    instigator_type=state.instigator_type.value,
                    instigator_body=serialize_value(state),
                )
            )
        except db_exc.IntegrityError:
            conn.execute(
                InstigatorsTable.update()
                .where(InstigatorsTable.c.selector_id == selector_id)
                .values(
                    status=state.status.value,
                    instigator_type=state.instigator_type.value,
                    instigator_body=serialize_value(state),
                    update_timestamp=pendulum.now("UTC"),
                )
            )

    def add_instigator_state(self, state: InstigatorState) -> InstigatorState:
        check.inst_param(state, "state", InstigatorState)
        with self.connect() as conn:
            try:
                conn.execute(
                    JobTable.insert().values(
                        job_origin_id=state.instigator_origin_id,
                        repository_origin_id=state.repository_origin_id,
                        status=state.status.value,
                        job_type=state.instigator_type.value,
                        job_body=serialize_value(state),
                    )
                )
            except db_exc.IntegrityError as exc:
                raise DagsterInvariantViolationError(
                    f"InstigatorState {state.instigator_origin_id} is already present in storage"
                ) from exc

            # try writing to the instigators table
            if self._has_instigators_table(conn):
                self._add_or_update_instigators_table(conn, state)

        return state

    def update_instigator_state(self, state: InstigatorState) -> InstigatorState:
        check.inst_param(state, "state", InstigatorState)
        if not self.get_instigator_state(state.instigator_origin_id, state.selector_id):
            raise DagsterInvariantViolationError(
                "InstigatorState {id} is not present in storage".format(
                    id=state.instigator_origin_id
                )
            )

        values = {
            "status": state.status.value,
            "job_body": serialize_value(state),
            "update_timestamp": pendulum.now("UTC"),
        }
        if self.has_instigators_table():
            values["selector_id"] = state.selector_id

        with self.connect() as conn:
            conn.execute(
                JobTable.update()
                .where(JobTable.c.job_origin_id == state.instigator_origin_id)
                .values(**values)
            )
            if self._has_instigators_table(conn):
                self._add_or_update_instigators_table(conn, state)

        return state

    def delete_instigator_state(self, origin_id: str, selector_id: str) -> None:
        check.str_param(origin_id, "origin_id")
        check.str_param(selector_id, "selector_id")

        if not self.get_instigator_state(origin_id, selector_id):
            raise DagsterInvariantViolationError(
                f"InstigatorState {origin_id} is not present in storage"
            )

        with self.connect() as conn:
            conn.execute(JobTable.delete().where(JobTable.c.job_origin_id == origin_id))

            if self._has_instigators_table(conn):
                if not self._jobs_has_selector_state(conn, selector_id):
                    conn.execute(
                        InstigatorsTable.delete().where(
                            InstigatorsTable.c.selector_id == selector_id
                        )
                    )

    def _jobs_has_selector_state(self, conn: Connection, selector_id: str) -> bool:
        query = (
            db_select([db.func.count()])
            .select_from(JobTable)
            .where(JobTable.c.selector_id == selector_id)
        )
        result = conn.execute(query)
        row = result.fetchone()
        result.close()
        return row[0] > 0  # type: ignore  # (possible none)

    def _add_filter_limit(
        self,
        query: SqlAlchemyQuery,
        before: Optional[float] = None,
        after: Optional[float] = None,
        limit: Optional[int] = None,
        statuses=None,
    ) -> SqlAlchemyQuery:
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
    def supports_batch_queries(self) -> bool:
        return self.has_instigators_table() and self.has_built_index(SCHEDULE_TICKS_SELECTOR_ID)

    def has_instigators_table(self) -> bool:
        with self.connect() as conn:
            return self._has_instigators_table(conn)

    def _has_instigators_table(self, conn: Connection) -> bool:
        table_names = db.inspect(conn).get_table_names()
        return "instigators" in table_names

    def _has_asset_daemon_asset_evaluations_table(self, conn: Connection) -> bool:
        table_names = db.inspect(conn).get_table_names()
        return "asset_daemon_asset_evaluations" in table_names

    def get_batch_ticks(
        self,
        selector_ids: Sequence[str],
        limit: Optional[int] = None,
        statuses: Optional[Sequence[TickStatus]] = None,
    ) -> Mapping[str, Sequence[InstigatorTick]]:
        check.sequence_param(selector_ids, "selector_ids", of_type=str)
        check.opt_int_param(limit, "limit")
        check.opt_sequence_param(statuses, "statuses", of_type=TickStatus)

        bucket_rank_column = (
            db.func.rank()
            .over(
                order_by=db.desc(JobTickTable.c.timestamp),
                partition_by=JobTickTable.c.selector_id,
            )
            .label("rank")
        )
        subquery = db_subquery(
            db_select(
                [
                    JobTickTable.c.id,
                    JobTickTable.c.selector_id,
                    JobTickTable.c.tick_body,
                    bucket_rank_column,
                ]
            )
            .select_from(JobTickTable)
            .where(JobTickTable.c.selector_id.in_(selector_ids))
        )
        if statuses:
            subquery = subquery.where(
                JobTickTable.c.status.in_([status.value for status in statuses])
            )

        query = (
            db_select([subquery.c.id, subquery.c.selector_id, subquery.c.tick_body])
            .order_by(subquery.c.rank.asc())
            .where(subquery.c.rank <= limit)
        )

        rows = self.execute(query)
        results = defaultdict(list)
        for row in rows:
            tick_id = row[0]
            selector_id = row[1]
            tick_data = deserialize_value(row[2], TickData)
            results[selector_id].append(InstigatorTick(tick_id, tick_data))
        return results

    def get_ticks(
        self,
        origin_id: str,
        selector_id: str,
        before: Optional[float] = None,
        after: Optional[float] = None,
        limit: Optional[int] = None,
        statuses: Optional[Sequence[TickStatus]] = None,
    ) -> Sequence[InstigatorTick]:
        check.str_param(origin_id, "origin_id")
        check.opt_float_param(before, "before")
        check.opt_float_param(after, "after")
        check.opt_int_param(limit, "limit")
        check.opt_list_param(statuses, "statuses", of_type=TickStatus)

        base_query = (
            db_select([JobTickTable.c.id, JobTickTable.c.tick_body])
            .select_from(JobTickTable)
            .order_by(JobTickTable.c.timestamp.desc())
        )
        if self.has_instigators_table():
            query = base_query.where(
                db.or_(
                    JobTickTable.c.selector_id == selector_id,
                    db.and_(
                        JobTickTable.c.selector_id.is_(None),
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
        return list(map(lambda r: InstigatorTick(r[0], deserialize_value(r[1], TickData)), rows))

    def create_tick(self, tick_data: TickData) -> InstigatorTick:
        check.inst_param(tick_data, "tick_data", TickData)

        values = {
            "job_origin_id": tick_data.instigator_origin_id,
            "status": tick_data.status.value,
            "type": tick_data.instigator_type.value,
            "timestamp": utc_datetime_from_timestamp(tick_data.timestamp),
            "tick_body": serialize_value(tick_data),
        }
        if self.has_instigators_table() and tick_data.selector_id:
            values["selector_id"] = tick_data.selector_id

        with self.connect() as conn:
            try:
                tick_insert = JobTickTable.insert().values(**values)
                result = conn.execute(tick_insert)
                tick_id = result.inserted_primary_key[0]
                return InstigatorTick(tick_id, tick_data)
            except db_exc.IntegrityError as exc:
                raise DagsterInvariantViolationError(
                    f"Unable to insert InstigatorTick for job {tick_data.instigator_name} in"
                    " storage"
                ) from exc

    def update_tick(self, tick: InstigatorTick) -> InstigatorTick:
        check.inst_param(tick, "tick", InstigatorTick)

        values = {
            "status": tick.status.value,
            "type": tick.instigator_type.value,
            "timestamp": utc_datetime_from_timestamp(tick.timestamp),
            "tick_body": serialize_value(tick.tick_data),
        }
        if self.has_instigators_table() and tick.selector_id:
            values["selector_id"] = tick.selector_id

        with self.connect() as conn:
            conn.execute(
                JobTickTable.update().where(JobTickTable.c.id == tick.tick_id).values(**values)
            )

        return tick

    def purge_ticks(
        self,
        origin_id: str,
        selector_id: str,
        before: float,
        tick_statuses: Optional[Sequence[TickStatus]] = None,
    ) -> None:
        check.str_param(origin_id, "origin_id")
        check.float_param(before, "before")
        check.opt_list_param(tick_statuses, "tick_statuses", of_type=TickStatus)

        utc_before = utc_datetime_from_timestamp(before)

        query = JobTickTable.delete().where(JobTickTable.c.timestamp < utc_before)
        if tick_statuses:
            query = query.where(
                JobTickTable.c.status.in_([tick_status.value for tick_status in tick_statuses])
            )

        if self.has_instigators_table():
            query = query.where(
                db.or_(
                    JobTickTable.c.selector_id == selector_id,
                    db.and_(
                        JobTickTable.c.selector_id.is_(None),
                        JobTickTable.c.job_origin_id == origin_id,
                    ),
                )
            )
        else:
            query = query.where(JobTickTable.c.job_origin_id == origin_id)

        with self.connect() as conn:
            conn.execute(query)

    @property
    def supports_auto_materialize_asset_evaluations(self) -> bool:
        with self.connect() as conn:
            return self._has_asset_daemon_asset_evaluations_table(conn)

    def add_auto_materialize_asset_evaluations(
        self,
        evaluation_id: int,
        asset_evaluations: Sequence[AutoMaterializeAssetEvaluation],
    ):
        if not asset_evaluations:
            return

        with self.connect() as conn:
            bulk_insert = AssetDaemonAssetEvaluationsTable.insert().values(
                [
                    {
                        "evaluation_id": evaluation_id,
                        "asset_key": evaluation.asset_key.to_string(),
                        "asset_evaluation_body": serialize_value(evaluation),
                        "num_requested": evaluation.num_requested,
                        "num_skipped": evaluation.num_skipped,
                        "num_discarded": evaluation.num_discarded,
                    }
                    for evaluation in asset_evaluations
                ]
            )
            conn.execute(bulk_insert)

    def get_auto_materialize_asset_evaluations(
        self, asset_key: AssetKey, limit: int, cursor: Optional[int] = None
    ) -> Sequence[AutoMaterializeAssetEvaluationRecord]:
        with self.connect() as conn:
            query = (
                db_select(
                    [
                        AssetDaemonAssetEvaluationsTable.c.id,
                        AssetDaemonAssetEvaluationsTable.c.asset_evaluation_body,
                        AssetDaemonAssetEvaluationsTable.c.evaluation_id,
                        AssetDaemonAssetEvaluationsTable.c.create_timestamp,
                    ]
                )
                .where(AssetDaemonAssetEvaluationsTable.c.asset_key == asset_key.to_string())
                .order_by(AssetDaemonAssetEvaluationsTable.c.evaluation_id.desc())
            ).limit(limit)

            if cursor:
                query = query.where(AssetDaemonAssetEvaluationsTable.c.evaluation_id < cursor)

            rows = db_fetch_mappings(conn, query)
            return [AutoMaterializeAssetEvaluationRecord.from_db_row(row) for row in rows]

    def purge_asset_evaluations(self, before: float):
        check.float_param(before, "before")

        utc_before = utc_datetime_from_timestamp(before)
        query = AssetDaemonAssetEvaluationsTable.delete().where(
            AssetDaemonAssetEvaluationsTable.c.create_timestamp < utc_before
        )

        with self.connect() as conn:
            conn.execute(query)

    def wipe(self) -> None:
        """Clears the schedule storage."""
        with self.connect() as conn:
            # https://stackoverflow.com/a/54386260/324449
            conn.execute(JobTable.delete())
            conn.execute(JobTickTable.delete())
            if self._has_instigators_table(conn):
                conn.execute(InstigatorsTable.delete())
            if self._has_asset_daemon_asset_evaluations_table(conn):
                conn.execute(AssetDaemonAssetEvaluationsTable.delete())

    # MIGRATIONS

    def has_secondary_index_table(self) -> bool:
        with self.connect() as conn:
            return "secondary_indexes" in db.inspect(conn).get_table_names()

    def has_built_index(self, migration_name: str) -> bool:
        if not self.has_secondary_index_table():
            return False

        query = (
            db_select([1])
            .where(SecondaryIndexMigrationTable.c.name == migration_name)
            .where(SecondaryIndexMigrationTable.c.migration_completed != None)  # noqa: E711
            .limit(1)
        )
        with self.connect() as conn:
            results = conn.execute(query).fetchall()

        return len(results) > 0

    def mark_index_built(self, migration_name: str) -> None:
        query = SecondaryIndexMigrationTable.insert().values(
            name=migration_name,
            migration_completed=datetime.now(),
        )
        with self.connect() as conn:
            try:
                conn.execute(query)
            except db_exc.IntegrityError:
                conn.execute(
                    SecondaryIndexMigrationTable.update()
                    .where(SecondaryIndexMigrationTable.c.name == migration_name)
                    .values(migration_completed=datetime.now())
                )

    def _execute_data_migrations(
        self,
        migrations: Mapping[str, Callable[..., Any]],
        print_fn: Optional[Callable] = None,
        force_rebuild_all: bool = False,
    ) -> None:
        for migration_name, migration_fn in migrations.items():
            if self.has_built_index(migration_name):
                if not force_rebuild_all:
                    if print_fn:
                        print_fn(f"Skipping already applied migration: {migration_name}")
                    continue
            if print_fn:
                print_fn(f"Starting data migration: {migration_name}")
            migration_fn()(self, print_fn)
            self.mark_index_built(migration_name)
            if print_fn:
                print_fn(f"Finished data migration: {migration_name}")

    def migrate(self, print_fn: Optional[PrintFn] = None, force_rebuild_all: bool = False) -> None:
        self._execute_data_migrations(
            REQUIRED_SCHEDULE_DATA_MIGRATIONS, print_fn, force_rebuild_all
        )

    def optimize(self, print_fn: Optional[PrintFn] = None, force_rebuild_all: bool = False) -> None:
        self._execute_data_migrations(
            OPTIONAL_SCHEDULE_DATA_MIGRATIONS, print_fn, force_rebuild_all
        )
