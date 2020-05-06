import copy
import os
import zipfile

from dagster import check


def subset_environment_dict(environment_dict, solid_name):
    '''Drops solid config for solids other than solid_name; this subsetting is required when
    executing a single solid on EMR to pass config validation.
    '''
    check.dict_param(environment_dict, 'environment_dict')
    check.str_param(solid_name, 'solid_name')

    subset = copy.deepcopy(environment_dict)
    if 'solids' in subset:
        solid_config_keys = list(subset['solids'].keys())
        for key in solid_config_keys:
            if key != solid_name:
                del subset['solids'][key]
    return subset


def build_pyspark_zip(zip_file, path):
    '''Archives the current path into a file named `zip_file`
    '''
    check.str_param(zip_file, 'zip_file')
    check.str_param(path, 'path')

    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(path):
            for fname in files:
                abs_fname = os.path.join(root, fname)

                # Skip various artifacts
                if 'pytest' in abs_fname or '__pycache__' in abs_fname or 'pyc' in abs_fname:
                    continue

                zf.write(abs_fname, os.path.relpath(os.path.join(root, fname), path))
