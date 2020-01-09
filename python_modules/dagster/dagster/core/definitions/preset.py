import os
from collections import namedtuple
from glob import glob

import six
import yaml

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.utils.yaml_utils import merge_yamls

from .mode import DEFAULT_MODE_NAME


class PresetDefinition(namedtuple('_PresetDefinition', 'name environment_dict solid_subset mode')):
    '''Defines a preset configuration in which a pipeline can execute.


    Presets can be used in Dagit to load predefined configurations into the tool.

    Presets may also be used from the Python API (in a script, or in test) as follows:

    .. code-block:: python

        execute_pipeline_with_preset(pipeline_def, 'example_preset')

    Presets may also be used with the command line tools:

    .. code-block:: shell

        $ dagster pipeline execute example_pipeline --preset example_preset
        $ dagster pipeline execute example_pipeline -p example_preset

    Args:
        name (str): The name of this preset. Must be unique in the presets defined on a given
            pipeline.
        environment_dict (Optional[dict]): A dict representing the config to set with the preset.
            This is equivalent to the ``environment_dict`` argument to :py:func:`execute_pipeline`.
        solid_subset (Optional[List[str]]): The list of names of solid invocations (i.e., of
            unaliased solids or of their aliases if aliased) to execute with this preset.
        mode (Optional[str]): The mode to apply when executing this preset. (default: 'default')
    '''

    @staticmethod
    def from_files(name, environment_files=None, solid_subset=None, mode=None):
        '''Static constructor for presets from YAML files.

        Args:
            name (str): The name of this preset. Must be unique in the presets defined on a given
                pipeline.
            environment_files (Optional[List[str]]): List of paths or glob patterns for yaml files
                to load and parse as the environment config for this preset.
            solid_subset (Optional[List[str]]): The list of names of solid invocations (i.e., of
                unaliased solids or of their aliases if aliased) to execute with this preset.
            mode (Optional[str]): The mode to apply when executing this preset. (default:
                'default')
        '''
        check.str_param(name, 'name')
        environment_files = check.opt_list_param(environment_files, 'environment_files')
        solid_subset = check.opt_nullable_list_param(solid_subset, 'solid_subset', of_type=str)
        mode = check.opt_str_param(mode, 'mode', DEFAULT_MODE_NAME)

        filenames = []
        for file_glob in environment_files or []:
            globbed_files = glob(file_glob)
            if not globbed_files:
                raise DagsterInvalidDefinitionError(
                    'File or glob pattern "{file_glob}" for "environment_files" in preset '
                    '"{name}" produced no results.'.format(name=name, file_glob=file_glob)
                )

            filenames += [os.path.realpath(globbed_file) for globbed_file in globbed_files]

        try:
            merged = merge_yamls(filenames)
        except yaml.YAMLError as err:
            six.raise_from(
                DagsterInvariantViolationError(
                    'Encountered error attempting to parse yaml. Parsing files {file_set} '
                    'loaded by file/patterns {files} on preset "{name}".'.format(
                        file_set=filenames, files=environment_files, name=name
                    )
                ),
                err,
            )

        return PresetDefinition(name, merged, solid_subset, mode)

    def __new__(cls, name, environment_dict=None, solid_subset=None, mode=None):
        return super(PresetDefinition, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            environment_dict=check.opt_dict_param(environment_dict, 'environment_dict'),
            solid_subset=check.opt_nullable_list_param(solid_subset, 'solid_subset', of_type=str),
            mode=check.opt_str_param(mode, 'mode', DEFAULT_MODE_NAME),
        )

    def get_environment_yaml(self):
        '''Get the environment dict set on a preset as YAML.

        Returns:
            str: The environment dict as YAML.
        '''
        return yaml.dump(self.environment_dict, default_flow_style=False)
