import os
from glob import glob

import six
import yaml

from dagster import check
from dagster.utils.yaml_utils import merge_yamls
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from .mode import DEFAULT_MODE_NAME


class PresetDefinition:
    '''Defines a preset configuration that a pipeline can execute in. Presets can be used in Dagit to
    load the predefined configuration in to the tool, or in a script or test as follows:

    .. code-block:: python

        execute_pipeline(**pipeline_def.get_preset('example'))


    Args:
        name (str):
            Name of this preset, must be unique amongst presets for a pipeline.
        environment_files (Optional[List[str]]):
            List of paths or glob patterns for yaml files to load and parse as the enivornment
            config for this preset.
        solid_subset (Optional[List[str]]):
            The list of names of solid invocations to execute for this preset.
        mode (Optional[str]):
            The mode to apply when executing this preset. Defaults to 'default'.
    '''

    def __init__(self, name, environment_files=None, solid_subset=None, mode=None):
        self.name = check.str_param(name, 'name')
        self.environment_files = check.opt_list_param(
            environment_files, 'environment_files', of_type=str
        )
        self.solid_subset = check.opt_nullable_list_param(solid_subset, 'solid_subset', of_type=str)
        self.mode = check.opt_str_param(mode, 'mode', DEFAULT_MODE_NAME)

    def get_environment_dict(self, pipeline_name):
        if self.environment_files is None:
            return None

        file_set = set()
        for file_glob in self.environment_files:
            files = glob(file_glob)
            if not files:
                raise DagsterInvalidDefinitionError(
                    'File or glob pattern "{file_glob}" for "environment_files" in preset '
                    '"{name}" for pipline "{pipeline}" produced no results.'.format(
                        name=self.name, file_glob=file_glob, pipeline=pipeline_name
                    )
                )

            file_set.update(map(os.path.realpath, files))

        try:
            merged = merge_yamls(list(file_set))
        except yaml.YAMLError as err:
            six.raise_from(
                DagsterInvariantViolationError(
                    'Encountered error attempting to parse yaml. Parsing files {file_set} '
                    'loaded by file/patterns {files} on preset "{name}" for pipeline "{pipeline}".'.format(
                        file_set=file_set,
                        files=self.environment_files,
                        name=self.name,
                        pipeline=pipeline_name,
                    )
                ),
                err,
            )

        return merged

    def get_environment_yaml(self, pipeline_name):
        merged = self.get_environment_dict(pipeline_name)
        if merged is None:
            return None

        return yaml.dump(merged, default_flow_style=False)
