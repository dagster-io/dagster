from collections import namedtuple

from dagster import check


class PipelineSelector(
    namedtuple('_PipelineSelector', 'location_name repository_name pipeline_name solid_selection')
):
    '''
    The information needed to resolve a pipeline within a host process.
    '''

    def __new__(
        cls, location_name, repository_name, pipeline_name, solid_selection,
    ):
        return super(PipelineSelector, cls).__new__(
            cls,
            location_name=check.str_param(location_name, 'location_name'),
            repository_name=check.str_param(repository_name, 'repository_name'),
            pipeline_name=check.str_param(pipeline_name, 'pipeline_name'),
            solid_selection=check.opt_nullable_list_param(solid_selection, 'solid_selection', str),
        )

    def to_graphql_input(self):
        return {
            'repositoryLocationName': self.location_name,
            'repositoryName': self.repository_name,
            'pipelineName': self.pipeline_name,
            'solidSubset': self.solid_selection,
        }

    def with_solid_selection(self, solid_selection):
        check.invariant(
            self.solid_selection is None,
            'Can not invoke with_solid_selection when solid_selection={} is already set'.format(
                solid_selection
            ),
        )
        return PipelineSelector(
            self.location_name, self.repository_name, self.pipeline_name, solid_selection
        )
