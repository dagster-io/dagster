from collections import namedtuple

from dagster import check


class PipelineSelector(
    namedtuple('_PipelineSelector', 'location_name repository_name pipeline_name solid_subset')
):
    '''
    The information needed to resolve a pipeline within a host process.
    '''

    def __new__(
        cls, location_name, repository_name, pipeline_name, solid_subset,
    ):
        return super(PipelineSelector, cls).__new__(
            cls,
            location_name=check.str_param(location_name, 'location_name'),
            repository_name=check.str_param(repository_name, 'repository_name'),
            pipeline_name=check.str_param(pipeline_name, 'pipeline_name'),
            solid_subset=check.opt_nullable_list_param(solid_subset, 'solid_subset', str),
        )

    def to_graphql_input(self):
        return {
            'repositoryLocationName': self.location_name,
            'repositoryName': self.repository_name,
            'pipelineName': self.pipeline_name,
            'solidSubset': self.solid_subset,
        }

    def with_solid_subset(self, solid_subset):
        check.invariant(
            self.solid_subset is None, 'Can not invoke with_solid_subset if one is already set'
        )
        return PipelineSelector(
            self.location_name, self.repository_name, self.pipeline_name, solid_subset
        )
