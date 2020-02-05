import copy
import os
import zipfile

import six

from dagster.utils import script_relative_path


def subset_environment_dict(environment_dict, solid_name):
    subset = copy.deepcopy(environment_dict)
    if 'solids' in subset:
        solid_config_keys = list(subset['solids'].keys())
        for key in solid_config_keys:
            if key != solid_name:
                del subset['solids'][key]
    return subset


def build_main_file(
    main_file, mode_name, pipeline_file, solid_name, environment_dict, pipeline_fn_name
):
    with open(script_relative_path('main.py.template'), 'rb') as f:
        main_template_str = six.ensure_str(f.read())

    with open(main_file, 'wb') as f:
        f.write(
            six.ensure_binary(
                main_template_str.format(
                    mode_name=mode_name,
                    pipeline_file=os.path.splitext(os.path.basename(pipeline_file))[0],
                    solid_name=solid_name,
                    environment_dict=subset_environment_dict(environment_dict, solid_name),
                    pipeline_fn_name=pipeline_fn_name,
                )
            )
        )


def build_pyspark_zip(zip_file, path):
    '''Archives the current path into a file named `zip_file`
    '''
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(path):
            for fname in files:
                abs_fname = os.path.join(root, fname)

                # Skip various artifacts
                if 'pytest' in abs_fname or '__pycache__' in abs_fname or 'pyc' in abs_fname:
                    continue

                zf.write(abs_fname, os.path.relpath(os.path.join(root, fname), path))
