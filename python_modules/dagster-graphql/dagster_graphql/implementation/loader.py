from collections import defaultdict

from dagster import check
from dagster.core.storage.pipeline_run import JobBucket, TagBucket


class BatchJobRunLoader:
    """
    Batch run loader, which fetches a number of runs for a set of jobs.  This can be used to
    instantiate a batch of graphene jobs, so that job runs can be fetched in a single database query
    instead of getting split out across multiple queries, without changing the structure of the
    graphql query.
    """

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
        runs = self._instance.get_runs(
            bucket=JobBucket(bucket_limit=limit, job_names=self._job_names),
        )
        self._data = defaultdict(list)
        for run in runs:
            self._data[run.pipeline_name].append(run)
        self._fetched_limit = limit
        self._fetched = True


class BatchTagRunLoader:
    """
    Batch run loader, which fetches a number of runs for a set of tag values corresponding to a
    given tag key. This can be used to instantiate a batch of graphene objects that map to a set of
    job runs using tags (e.g. schedules, sensors, partitions). These tagged job runs can be fetched
    in a single database query instead of getting split out across multiple queries, without
    changing the structure of the graphql query.
    """

    def __init__(self, graphene_info, tag_key, tag_values):
        self._instance = graphene_info.context.instance
        self._tag_key = check.str_param(tag_key, "tag_key")
        self._tag_values = check.list_param(tag_values, "tag_values", of_type=str)
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
            bucket=TagBucket(
                tag_key=self._tag_key, bucket_limit=limit, tag_values=self._tag_values
            ),
        )
        self._data = defaultdict(list)
        for run in runs:
            self._data[run.tags.get(self._tag_key)].append(run)
        self._fetched_limit = limit
        self._fetched = True
