from collections import defaultdict

from dagster import check
from dagster.core.storage.pipeline_run import RunBucketLimit


class BatchJobRunLoader:
    def __init__(self, graphene_info, job_names):
        self._instance = graphene_info.context.instance
        self._job_names = check.list_param(job_names, "job_names", of_type=str)
        self._fetched = False
        self._fetched_limit = None
        self._data = None

    def get_runs_for_job(self, job_name, limit):
        check.invariant(job_name in self._job_names)
        if not self._fetched or limit > self._fetched_limit:
            self.fetch(limit)
        return self._data[job_name][:limit]

    def fetch(self, limit):
        runs = self._instance.get_runs(limit=RunBucketLimit.by_job(bucket_limit=limit))
        self._data = defaultdict(list)
        for run in runs:
            self._data[run.pipeline_name].append(run)
        self._fetched_limit = limit
        self._fetched = True


class BatchTagRunLoader:
    def __init__(self, graphene_info, tag_key):
        self._instance = graphene_info.context.instance
        self._tag_key = check.str_param(tag_key, "tag_key")
        self._fetched = False
        self._fetched_limit = None
        self._data = None

    @property
    def tag_key(self):
        return self._tag_key

    def get_runs_for_tag(self, tag_value, limit):
        if not self._fetched or limit > self._fetched_limit:
            self.fetch(limit)
        return self._data[tag_value][:limit]

    def fetch(self, limit):
        runs = self._instance.get_runs(
            limit=RunBucketLimit.by_tag(self._tag_key, bucket_limit=limit)
        )
        self._data = defaultdict(list)
        for run in runs:
            self._data[run.tags.get(self._tag_key)].append(run)
        self._fetched_limit = limit
        self._fetched = True
