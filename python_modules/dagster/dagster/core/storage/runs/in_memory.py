from collections import OrderedDict, defaultdict

from dagster import check
from dagster.core.events import DagsterEvent, DagsterEventType

from ..pipeline_run import PipelineRun, PipelineRunStatus
from .base import RunStorage


class InMemoryRunStorage(RunStorage):
    def __init__(self):
        self._runs = OrderedDict()
        self._run_tags = defaultdict(set)

    def add_run(self, pipeline_run):
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)
        check.invariant(
            not self._runs.get(pipeline_run.run_id),
            'Can not add same run twice for run_id {run_id}'.format(run_id=pipeline_run.run_id),
        )

        self._runs[pipeline_run.run_id] = pipeline_run
        if pipeline_run.tags and len(pipeline_run.tags) > 0:
            for k, v in pipeline_run.tags.items():
                self._run_tags[k].add(v)

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

    def all_runs(self, cursor=None, limit=None):
        return self._slice(list(self._runs.values())[::-1], cursor, limit)

    def get_runs_with_pipeline_name(self, pipeline_name, cursor=None, limit=None):
        check.str_param(pipeline_name, 'pipeline_name')
        return self._slice(
            [r for r in self.all_runs() if r.pipeline_name == pipeline_name], cursor, limit
        )

    def get_run_count_with_matching_tags(self, tags):
        check.list_param(tags, 'tags', tuple)
        return len(self.get_runs_with_matching_tags(tags))

    def get_runs_with_matching_tags(self, tags, cursor=None, limit=None):
        check.list_param(tags, 'tags', tuple)

        return self._slice(
            [r for r in self.all_runs() if all(r.tags.get(key) == value for key, value in tags)],
            cursor,
            limit,
        )

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
        return sorted([(k, v) for k, v in self._run_tags.items()], key=lambda x: x[0])

    def get_runs_with_status(self, run_status, cursor=None, limit=None):
        check.inst_param(run_status, 'run_status', PipelineRunStatus)
        matching_runs = list(
            filter(lambda run: run.status == run_status, reversed(self._runs.values()))
        )
        return self._slice(matching_runs, cursor=cursor, limit=limit)

    def has_run(self, run_id):
        check.str_param(run_id, 'run_id')
        return run_id in self._runs

    def delete_run(self, run_id):
        check.str_param(run_id, 'run_id')
        del self._runs[run_id]

    def wipe(self):
        self._runs = OrderedDict()
