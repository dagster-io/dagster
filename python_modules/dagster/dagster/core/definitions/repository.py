from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from .pipeline import PipelineDefinition


class RepositoryDefinition(object):
    '''Define a repository that contains a collection of pipelines.

    Attributes:
        name (str): The name of the pipeline.
        pipeline_dict (Dict[str, callable]):
            An dictionary of pipelines. The value of the dictionary is a function that takes
            no parameters and returns a PipelineDefiniton.

            We pass callables instead of the PipelineDefinitions itself so that they can be
            created on demand when accessed by name.

            As the pipelines are retrieved it ensures that the keys of the dictionary and the
            name of the pipeline are the same.

    '''

    def __init__(self, name, pipeline_dict, enforce_uniqueness=True):
        '''
        Args:
            name (str): Name of pipeline.
            pipeline_dict (Dict[str, callable]): See top-level class documentation
        '''
        self.name = check.str_param(name, 'name')

        check.dict_param(pipeline_dict, 'pipeline_dict', key_type=str)

        for val in pipeline_dict.values():
            check.is_callable(val, 'Value in pipeline_dict must be function')

        self.pipeline_dict = pipeline_dict

        self._pipeline_cache = {}

        self.enforce_uniqueness = enforce_uniqueness

    def has_pipeline(self, name):
        check.str_param(name, 'name')
        return name in self.pipeline_dict

    def get_pipeline(self, name):
        '''Get a pipeline by name. Only constructs that pipeline and caches it.

        Args:
            name (str): Name of the pipeline to retriever

        Returns:
            PipelineDefinition: Instance of PipelineDefinition with that name.
'''
        check.str_param(name, 'name')

        if name in self._pipeline_cache:
            return self._pipeline_cache[name]

        try:
            pipeline = self.pipeline_dict[name]()
        except KeyError:
            raise check.CheckError(
                'Could not find pipeline "{name}". Found: {pipeline_names}.'.format(
                    name=name,
                    pipeline_names=', '.join(
                        [
                            '"{pipeline_name}"'.format(pipeline_name=pipeline_name)
                            for pipeline_name in self.pipeline_dict.keys()
                        ]
                    ),
                )
            )
        check.invariant(
            pipeline.name == name,
            'Name does not match. Name in dict {name}. Name in pipeline {pipeline.name}'.format(
                name=name, pipeline=pipeline
            ),
        )

        self._pipeline_cache[name] = check.inst(
            pipeline,
            PipelineDefinition,
            'Function passed into pipeline_dict with key {key} must return a PipelineDefinition'.format(
                key=name
            ),
        )

        return pipeline

    def iterate_over_pipelines(self):
        '''Yield all pipelines one at a time

        Returns:
            Iterable[PipelineDefinition]:
        '''
        for name in self.pipeline_dict.keys():
            yield self.get_pipeline(name)

    def get_all_pipelines(self):
        '''Return all pipelines as a list

        Returns:
            List[PipelineDefinition]:

        '''
        pipelines = list(self.iterate_over_pipelines())

        self._construct_solid_defs(pipelines)

        return pipelines

    def _construct_solid_defs(self, pipelines):
        solid_defs = {}
        solid_to_pipeline = {}
        for pipeline in pipelines:
            for solid_def in pipeline.solid_defs:
                if solid_def.name not in solid_defs:
                    solid_defs[solid_def.name] = solid_def
                    solid_to_pipeline[solid_def.name] = pipeline.name
                elif self.enforce_uniqueness:
                    if not solid_defs[solid_def.name] is solid_def:
                        raise DagsterInvalidDefinitionError(
                            'Trying to add duplicate solid def {} in {}, Already saw in {}'.format(
                                solid_def.name, pipeline.name, solid_to_pipeline[solid_def.name]
                            )
                        )
        return solid_defs

    def get_solid_def(self, name):
        check.str_param(name, 'name')

        if not self.enforce_uniqueness:
            raise DagsterInvariantViolationError(
                (
                    'In order for get_solid_def to have reliable semantics '
                    'you must construct the repo with ensure_uniqueness=True'
                )
            )

        solid_defs = self._construct_solid_defs(self.get_all_pipelines())

        if name not in solid_defs:
            check.failed('could not find solid_def {}'.format(name))

        return solid_defs[name]

    def solid_def_named(self, name):
        check.str_param(name, 'name')
        for pipeline in self.get_all_pipelines():
            for solid in pipeline.solids:
                if solid.definition.name == name:
                    return solid.definition

        check.failed('Did not find ' + name)
