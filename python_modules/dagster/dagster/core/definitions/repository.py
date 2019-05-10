import os
from collections import namedtuple
from glob import glob

import six
import yaml

from dagster import check
from dagster.core.definitions import LoaderEntrypoint
from dagster.core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
    InvalidPipelineLoadingComboError,
    InvalidRepositoryLoadingComboError,
)
from dagster.utils.yaml_utils import merge_yamls

from .pipeline import PipelineDefinition

EPHEMERAL_NAME = '<<unnamed>>'


class RepositoryTargetInfo(
    namedtuple('_RepositoryTargetInfo', 'repository_yaml module_name python_file fn_name')
):
    def get_entrypoint(self):
        def _repo_load_invariant(condition):
            if not condition:
                raise InvalidRepositoryLoadingComboError()

        if self.repository_yaml:
            _repo_load_invariant(self.module_name is None)
            _repo_load_invariant(self.python_file is None)
            _repo_load_invariant(self.fn_name is None)
            return LoaderEntrypoint.from_yaml(self.repository_yaml)
        elif self.module_name and self.fn_name:
            _repo_load_invariant(self.repository_yaml is None)
            _repo_load_invariant(self.python_file is None)
            return LoaderEntrypoint.from_module_target(
                module_name=self.module_name, fn_name=self.fn_name
            )
        elif self.python_file and self.fn_name:
            _repo_load_invariant(self.repository_yaml is None)
            _repo_load_invariant(self.module_name is None)
            return LoaderEntrypoint.from_file_target(
                python_file=self.python_file, fn_name=self.fn_name
            )
        else:
            raise InvalidRepositoryLoadingComboError()


class RepositoryDefinition(object):
    '''Define a repository that contains a collection of pipelines.

    Args:
        name (str): The name of the pipeline.
        pipeline_dict (Dict[str, callable]):
            An dictionary of pipelines. The value of the dictionary is a function that takes
            no parameters and returns a PipelineDefiniton.

            We pass callables instead of the PipelineDefinitions itself so that they can be
            created on demand when accessed by name.

            As the pipelines are retrieved it ensures that the keys of the dictionary and the
            name of the pipeline are the same.
        repo_config (Optional[dict]):
            Preset configurations for pipelines such as environments and execution subsets

    '''

    def __init__(self, name, pipeline_dict, repo_config=None, enforce_solid_def_uniqueness=True):
        self.name = check.str_param(name, 'name')

        check.dict_param(pipeline_dict, 'pipeline_dict', key_type=str)

        for val in pipeline_dict.values():
            check.is_callable(val, 'Value in pipeline_dict must be function')

        self.pipeline_dict = pipeline_dict

        self._pipeline_cache = {}

        self.repo_config = check.opt_dict_param(repo_config, 'repo_config')

        self.enforce_solid_def_uniqueness = check.bool_param(
            enforce_solid_def_uniqueness, 'enforce_solid_def_uniqueness'
        )

    @staticmethod
    def eager_construction(name, pipelines, *args, **kwargs):
        '''Useful help when you are unconcerned about the the performance of
        pipeline construction. You can just pass a list of pipelines and it will
        handle constructing the dictionary of pipeline name to functions for you'''

        check.list_param(pipelines, 'pipelines', of_type=PipelineDefinition)

        # avoids lint violation cell-var-from-loop and crazy loop scoping rules
        # see https://stackoverflow.com/questions/12423614/
        def lambdify(item):
            return lambda: item

        return RepositoryDefinition(
            name, {pipeline.name: lambdify(pipeline) for pipeline in pipelines}, *args, **kwargs
        )

    @staticmethod
    def load_for_target_info(repo_target_info):
        '''Builds a RepositoryDefinition from a RepositoryTargetInfo object.
        '''
        check.inst_param(repo_target_info, 'repo_target_info', RepositoryTargetInfo)
        entrypoint = repo_target_info.get_entrypoint()

        obj = entrypoint.perform_load()

        if isinstance(obj, RepositoryDefinition):
            return obj
        elif isinstance(obj, PipelineDefinition):
            return RepositoryDefinition(name=EPHEMERAL_NAME, pipeline_dict={obj.name: lambda: obj})
        else:
            raise InvalidPipelineLoadingComboError(
                'entry point must return a repository or pipeline'
            )

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
            raise DagsterInvariantViolationError(
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
            (
                'Function passed into pipeline_dict with key {key} must return a '
                'PipelineDefinition'
            ).format(key=name),
        )

        return pipeline

    def get_all_pipelines(self):
        '''Return all pipelines as a list

        Returns:
            List[PipelineDefinition]:

        '''
        pipelines = list(map(self.get_pipeline, self.pipeline_dict.keys()))
        # This does uniqueness check
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

                if (
                    self.enforce_solid_def_uniqueness
                    and not solid_defs[solid_def.name] is solid_def
                ):
                    first_name, second_name = sorted(
                        [solid_to_pipeline[solid_def.name], pipeline.name]
                    )
                    raise DagsterInvalidDefinitionError(
                        (
                            'You have defined two solids named "{solid_def_name}" '
                            'in repository "{repository_name}". Solid names must be '
                            'unique within a repository. The solid has been defined in '
                            'pipeline "{first_pipeline_name}" and it has been defined '
                            'again in pipeline "{second_pipeline_name}."'
                        ).format(
                            solid_def_name=solid_def.name,
                            repository_name=self.name,
                            first_pipeline_name=first_name,
                            second_pipeline_name=second_name,
                        )
                    )

        return solid_defs

    def get_solid_def(self, name):
        check.str_param(name, 'name')

        if not self.enforce_solid_def_uniqueness:
            raise DagsterInvariantViolationError(
                (
                    'Cannot use get_solid_def in repo {} since solid def uniqueness '
                    'is not enforced'
                ).format(self.name)
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

    def get_preset(self, pipeline_name, solid_name):
        check.str_param(pipeline_name, 'pipeline_name')
        check.str_param(solid_name, 'solid_name')
        return self.get_presets_for_pipeline(pipeline_name).get(solid_name)

    def get_presets_for_pipeline(self, pipeline_name):
        if not (self.repo_config and self.repo_config.get('pipelines')):
            return {}

        presets = self.repo_config['pipelines'].get(pipeline_name, {}).get('presets', {})

        return {
            name: PipelinePreset(
                name, pipeline_name, config.get('solid_subset'), config.get('environment_files')
            )
            for name, config in presets.items()
        }

    def get_preset_pipeline(self, pipeline_name, preset_name):
        pipeline = self.get_pipeline(pipeline_name)
        preset = self.get_preset(pipeline_name, preset_name)
        if not preset:
            preset_names = [name for name in self.get_presets_for_pipeline(pipeline_name)]
            raise DagsterInvariantViolationError(
                (
                    'Could not find preset for "{preset_name}". Available presets '
                    'for pipeline "{pipeline_name}" are {preset_names}.'
                ).format(
                    preset_name=preset_name, preset_names=preset_names, pipeline_name=pipeline_name
                )
            )

        if not preset.solid_subset is None:
            pipeline = pipeline.build_sub_pipeline(preset.solid_subset)

        return {'pipeline': pipeline, 'environment_dict': preset.environment_dict}


class PipelinePreset(
    namedtuple('_PipelinePreset', 'name pipeline_name solid_subset environment_files')
):
    def __new__(cls, name, pipeline_name, solid_subset=None, environment_files=None):
        return super(PipelinePreset, cls).__new__(
            cls,
            check.str_param(name, 'name'),
            check.str_param(pipeline_name, 'pipeline_name'),
            check.opt_nullable_list_param(solid_subset, 'solid_subset', of_type=str),
            check.opt_nullable_list_param(environment_files, 'environment_files'),
        )

    @property
    def environment_dict(self):
        if self.environment_files is None:
            return None

        file_set = set()
        for file_glob in self.environment_files:
            files = glob(file_glob)
            if not files:
                raise DagsterInvalidDefinitionError(
                    'File or glob pattern "{file_glob}" for "environment_files" in preset "{name}" for '
                    'pipeline "{pipeline_name}" produced no results.'.format(
                        name=self.name, file_glob=file_glob, pipeline_name=self.pipeline_name
                    )
                )

            file_set.update(map(os.path.realpath, files))

        try:
            merged = merge_yamls(list(file_set))
        except yaml.YAMLError as err:
            six.raise_from(
                DagsterInvariantViolationError(
                    'Encountered error attempting to parse yaml. Parsing files {file_set} loaded by '
                    'file/patterns {files} on preset "{name}" for pipeline "{pipeline_name}".'.format(
                        file_set=file_set,
                        files=self.environment_files,
                        name=self.name,
                        pipeline_name=self.pipeline_name,
                    )
                ),
                err,
            )

        return merged

    @property
    def environment_yaml(self):
        merged = self.environment_dict
        if merged is None:
            return None

        return yaml.dump(merged, default_flow_style=False)
