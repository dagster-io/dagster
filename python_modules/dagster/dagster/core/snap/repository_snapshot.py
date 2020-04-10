from collections import OrderedDict, namedtuple

from dagster import RepositoryDefinition, check
from dagster.core.snap.pipeline_snapshot import PipelineIndex, PipelineSnapshot
from dagster.serdes import whitelist_for_serdes


class RepositoryIndex:
    def __init__(self, repository_snapshot):
        self.repository_snapshot = check.inst_param(
            repository_snapshot, 'repository_snapshot', RepositorySnapshot
        )
        self._pipeline_index_map = OrderedDict(
            (pipeline_snapshot.name, PipelineIndex(pipeline_snapshot))
            for pipeline_snapshot in repository_snapshot.pipeline_snapshots
        )

    def get_pipeline_index(self, pipeline_name):
        return self._pipeline_index_map[pipeline_name]

    def has_pipeline_index(self, pipeline_name):
        return pipeline_name in self._pipeline_index_map

    def get_pipeline_indices(self):
        return self._pipeline_index_map.values()

    @staticmethod
    def from_repository_def(repository_definition):
        return RepositoryIndex(RepositorySnapshot.from_repository_definition(repository_definition))


@whitelist_for_serdes
class RepositorySnapshot(namedtuple('_RepositorySnapshot', 'name pipeline_snapshots')):
    def __new__(cls, name, pipeline_snapshots):
        return super(RepositorySnapshot, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            pipeline_snapshots=check.list_param(
                pipeline_snapshots, 'pipeline_snapshots', of_type=PipelineSnapshot
            ),
        )

    def has_pipeline_snapshot(self, pipeline_name):
        check.str_param(pipeline_name, 'pipeline_name')
        for pipeline in self.pipeline_snapshots:
            if pipeline.name == pipeline_name:
                return True
        return False

    def get_pipeline_snapshot(self, pipeline_name):
        check.str_param(pipeline_name, 'pipeline_name')
        for pipeline in self.pipeline_snapshots:
            if pipeline.name == pipeline_name:
                return pipeline
        check.failed('pipeline not found')

    def get_all_pipeline_snapshots(self):
        return self.pipeline_snapshots

    @staticmethod
    def from_repository_definition(repository_definition):
        check.inst_param(repository_definition, 'repository_definition', RepositoryDefinition)
        return RepositorySnapshot(
            name=repository_definition.name,
            pipeline_snapshots=[
                PipelineSnapshot.from_pipeline_def(pipeline_definition)
                for pipeline_definition in repository_definition.get_all_pipelines()
            ],
        )
