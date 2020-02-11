from collections import OrderedDict, defaultdict

from dagster import check
from dagster.core.definitions.pipeline import PipelineRunsFilter
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.utils import frozendict

from ..pipeline_run import PipelineRun, PipelineRunStatus
from .base import RunStorage


class InMemoryRunStorage(RunStorage):
    def __init__(self):
        self._runs = OrderedDict()
        self._run_tags = defaultdict(dict)

    def add_run(self, pipeline_run):
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        check.invariant(
            not self._runs.get(pipeline_run.run_id),
            'Can not add same run twice for run_id {run_id}'.format(run_id=pipeline_run.run_id),
        )

        self._runs[pipeline_run.run_id] = pipeline_run
        if pipeline_run.tags and len(pipeline_run.tags) > 0:
            self._run_tags[pipeline_run.run_id] = frozendict(pipeline_run.tags)

        return pipeline_run

    def handle_run_event(self, run_id, event):
        check.str_param(run_id, 'run_id')
        check.inst_param(event, 'event', DagsterEvent)
        run = self._runs[run_id]

        if event.event_type == DagsterEventType.PIPELINE_START:
            self._runs[run_id] = run.run_with_status(PipelineRunStatus.STARTED)
        elif event.event_type == DagsterEventType.PIPELINE_SUCCESS:
            self._runs[run_id] = run.run_with_status(PipelineRunStatus.SUCCESS)
        elif event.event_type == DagsterEventType.PIPELINE_FAILURE:
            self._runs[run_id] = self._runs[run_id].run_with_status(PipelineRunStatus.FAILURE)

    def get_runs(self, filters=None, cursor=None, limit=None):
        check.opt_inst_param(filters, 'filters', PipelineRunsFilter)
        check.opt_str_param(cursor, 'cursor')
        check.opt_int_param(limit, 'limit')

        if not filters:
            return self._slice(list(self._runs.values())[::-1], cursor, limit)

        def run_filter(run):
            if filters.run_id and filters.run_id != run.run_id:
                return False

            if filters.status and filters.status != run.status:
                return False

            if filters.pipeline_name and filters.pipeline_name != run.pipeline_name:
                return False

            if filters.tags and not all(
                run.tags.get(key) == value for key, value in filters.tags.items()
            ):
                return False

            return True

        matching_runs = list(filter(run_filter, reversed(self._runs.values())))
        return self._slice(matching_runs, cursor=cursor, limit=limit)

    def get_runs_count(self, filters=None):
        check.opt_inst_param(filters, 'filters', PipelineRunsFilter)

        return len(self.get_runs(filters))

    def _slice(self, runs, cursor, limit):
        if cursor:
            try:
                index = next(i for i, run in enumerate(runs) if run.run_id == cursor)
            except StopIteration:
                return []
            start = index + 1
        else:
            start = 0

        if limit:
            end = start + limit
        else:
            end = None

        return list(runs)[start:end]

    def get_run_by_id(self, run_id):
        check.str_param(run_id, 'run_id')
        return self._runs.get(run_id)

    def get_run_tags(self):
        all_tags = defaultdict(set)
        for _run_id, tags in self._run_tags.items():
            for k, v in tags.items():
                all_tags[k].add(v)

        return sorted([(k, v) for k, v in all_tags.items()], key=lambda x: x[0])

    def has_run(self, run_id):
        check.str_param(run_id, 'run_id')
        return run_id in self._runs

    def delete_run(self, run_id):
        check.str_param(run_id, 'run_id')
        del self._runs[run_id]
        if run_id in self._run_tags:
            del self._run_tags[run_id]

    def wipe(self):
        self._runs = OrderedDict()
