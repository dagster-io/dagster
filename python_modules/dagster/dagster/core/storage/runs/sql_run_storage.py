from abc import abstractmethod
from collections import defaultdict
from datetime import datetime

import six
import sqlalchemy as db

from dagster import check
from dagster.core.definitions.pipeline import PipelineRunsFilter
from dagster.core.errors import DagsterRunAlreadyExists
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple

from ..pipeline_run import PipelineRun, PipelineRunStatus
from .base import RunStorage
from .schema import RunTagsTable, RunsTable


class SqlRunStorage(RunStorage):  # pylint: disable=no-init
    @abstractmethod
    def connect(self):
        '''Context manager yielding a sqlalchemy.engine.Connection.'''

    @abstractmethod
    def upgrade(self):
        '''This method should perform any schema or data migrations necessary to bring an
        out-of-date instance of the storage up to date.
        '''

    def execute(self, query):
        with self.connect() as conn:
            result_proxy = conn.execute(query)
            res = result_proxy.fetchall()
            result_proxy.close()

        return res

    def add_run(self, pipeline_run):
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

        with self.connect() as conn:
            try:
                runs_insert = RunsTable.insert().values(  # pylint: disable=no-value-for-parameter
                    run_id=pipeline_run.run_id,
                    pipeline_name=pipeline_run.pipeline_name,
                    status=pipeline_run.status.value,
                    run_body=serialize_dagster_namedtuple(pipeline_run),
                )
                conn.execute(runs_insert)
            except db.exc.IntegrityError as exc:
                six.raise_from(DagsterRunAlreadyExists, exc)

            if pipeline_run.tags and len(pipeline_run.tags) > 0:
                conn.execute(
                    RunTagsTable.insert(),  # pylint: disable=no-value-for-parameter
                    [
                        dict(run_id=pipeline_run.run_id, key=k, value=v)
                        for k, v in pipeline_run.tags.items()
                    ],
                )

        return pipeline_run

    def handle_run_event(self, run_id, event):
        check.str_param(run_id, 'run_id')
        check.inst_param(event, 'event', DagsterEvent)

        lookup = {
            DagsterEventType.PIPELINE_START: PipelineRunStatus.STARTED,
            DagsterEventType.PIPELINE_SUCCESS: PipelineRunStatus.SUCCESS,
            DagsterEventType.PIPELINE_FAILURE: PipelineRunStatus.FAILURE,
        }

        if event.event_type not in lookup:
            return

        run = self.get_run_by_id(run_id)
        if not run:
            # TODO log?
            return

        new_pipeline_status = lookup[event.event_type]

        with self.connect() as conn:
            conn.execute(
                RunsTable.update()  # pylint: disable=no-value-for-parameter
                .where(RunsTable.c.run_id == run_id)
                .values(
                    status=new_pipeline_status.value,
                    run_body=serialize_dagster_namedtuple(run.run_with_status(new_pipeline_status)),
                    update_timestamp=datetime.now(),
                )
            )

    def _rows_to_runs(self, rows):
        return list(map(lambda r: deserialize_json_to_dagster_namedtuple(r[0]), rows))

    def _add_cursor_limit_to_query(self, query, cursor, limit):
        ''' Helper function to deal with cursor/limit pagination args '''

        if cursor:
            cursor_query = db.select([RunsTable.c.id]).where(RunsTable.c.run_id == cursor)
            query = query.where(RunsTable.c.id < cursor_query)

        if limit:
            query = query.limit(limit)

        query = query.order_by(RunsTable.c.id.desc())
        return query

    def _add_filters_to_query(self, query, filters):
        check.inst_param(filters, 'filters', PipelineRunsFilter)

        if filters.run_id:
            query = query.where(RunsTable.c.run_id == filters.run_id)

        if filters.pipeline_name:
            query = query.where(RunsTable.c.pipeline_name == filters.pipeline_name)

        if filters.status:
            query = query.where(RunsTable.c.status == filters.status.value)

        if filters.tags:
            query = query.where(
                db.or_(
                    *(
                        db.and_(RunTagsTable.c.key == key, RunTagsTable.c.value == value)
                        for key, value in filters.tags.items()
                    )
                )
            ).group_by(RunsTable.c.run_body, RunsTable.c.id)

            if len(filters.tags) > 0:
                query = query.having(db.func.count(RunsTable.c.run_id) == len(filters.tags))

        return query

    def get_runs(self, filters=None, cursor=None, limit=None):
        filters = check.opt_inst_param(
            filters, 'filters', PipelineRunsFilter, default=PipelineRunsFilter()
        )
        check.opt_str_param(cursor, 'cursor')
        check.opt_int_param(limit, 'limit')

        # If we have a tags filter, then we need to select from a joined table
        if filters.tags:
            base_query = db.select([RunsTable.c.run_body]).select_from(
                RunsTable.outerjoin(RunTagsTable, RunsTable.c.run_id == RunTagsTable.c.run_id)
            )
        else:
            base_query = db.select([RunsTable.c.run_body]).select_from(RunsTable)

        query = self._add_filters_to_query(base_query, filters)
        query = self._add_cursor_limit_to_query(query, cursor, limit)
        rows = self.execute(query)
        return self._rows_to_runs(rows)

    def get_runs_count(self, filters=None):
        filters = check.opt_inst_param(
            filters, 'filters', PipelineRunsFilter, default=PipelineRunsFilter()
        )

        # If we have a tags filter, then we need to select from a joined table
        if filters.tags:
            subquery = db.select([1]).select_from(
                RunsTable.outerjoin(RunTagsTable, RunsTable.c.run_id == RunTagsTable.c.run_id)
            )
        else:
            subquery = db.select([1]).select_from(RunsTable)

        subquery = self._add_filters_to_query(subquery, filters)

        # We use an alias here because Postgres requires subqueries to be
        # aliased.
        subquery = subquery.alias("subquery")

        query = db.select([db.func.count()]).select_from(subquery)
        rows = self.execute(query)
        count = rows[0][0]
        return count

    def get_run_by_id(self, run_id):
        '''Get a run by its id.

        Args:
            run_id (str): The id of the run

        Returns:
            Optional[PipelineRun]
        '''
        check.str_param(run_id, 'run_id')

        query = db.select([RunsTable.c.run_body]).where(RunsTable.c.run_id == run_id)
        rows = self.execute(query)
        return deserialize_json_to_dagster_namedtuple(rows[0][0]) if len(rows) else None

    def get_run_tags(self):
        result = defaultdict(set)
        query = db.select([RunTagsTable.c.key, RunTagsTable.c.value]).distinct(RunTagsTable.c.value)
        rows = self.execute(query)
        for r in rows:
            result[r[0]].add(r[1])
        return sorted(list([(k, v) for k, v in result.items()]), key=lambda x: x[0])

    def has_run(self, run_id):
        check.str_param(run_id, 'run_id')
        return bool(self.get_run_by_id(run_id))

    def delete_run(self, run_id):
        check.str_param(run_id, 'run_id')
        query = db.delete(RunsTable).where(RunsTable.c.run_id == run_id)
        with self.connect() as conn:
            conn.execute(query)

    def wipe(self):
        '''Clears the run storage.'''
        with self.connect() as conn:
            # https://stackoverflow.com/a/54386260/324449
            conn.execute(RunsTable.delete())  # pylint: disable=no-value-for-parameter
            conn.execute(RunTagsTable.delete())  # pylint: disable=no-value-for-parameter
