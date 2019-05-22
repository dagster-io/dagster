import os
from glob import glob

import six
import yaml

from dagster import check
from dagster.utils.yaml_utils import merge_yamls
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from .mode import DEFAULT_MODE_NAME


class PresetDefinition:
    def __init__(self, name, environment_files=None, solid_subset=None, mode=None):
        self.name = check.str_param(name, 'name')
        self.environment_files = check.opt_list_param(
            environment_files, 'environment_files', of_type=str
        )
        self.solid_subset = check.opt_nullable_list_param(solid_subset, 'solid_subset', of_type=str)
        self.mode = check.opt_str_param(mode, 'mode', DEFAULT_MODE_NAME)

    @property
    def environment_dict(self):
        if self.environment_files is None:
            return None

        file_set = set()
        for file_glob in self.environment_files:
            files = glob(file_glob)
            if not files:
                raise DagsterInvalidDefinitionError(
                    'File or glob pattern "{file_glob}" for "environment_files" in preset '
                    '"{name}" produced no results.'.format(name=self.name, file_glob=file_glob)
                )

            file_set.update(map(os.path.realpath, files))

        try:
            merged = merge_yamls(list(file_set))
        except yaml.YAMLError as err:
            six.raise_from(
                DagsterInvariantViolationError(
                    'Encountered error attempting to parse yaml. Parsing files {file_set} '
                    'loaded by file/patterns {files} on preset "{name}".'.format(
                        file_set=file_set, files=self.environment_files, name=self.name
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
