#!/usr/bin/env python3

"""
To use, run
 python bin/create_library.py --name library_name
"""
from __future__ import absolute_import

import os
import shutil
import sys

import click

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, BASE_PATH)

from git_utils import get_most_recent_git_tag  # isort:skip


def copy_directory(src, dest):
    try:
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns('.DS_Store'))
    # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)


@click.command()
@click.option('--name', prompt='Name of library', help='Name of library')
def main(name):
    template_library_path = os.path.abspath('bin/assets/dagster-library-tmpl')
    new_template_library_path = os.path.abspath(
        'python_modules/libraries/dagster-{name}'.format(name=name)
    )

    if os.path.exists(new_template_library_path):
        raise click.UsageError('Library with name {name} already exists'.format(name=name))

    copy_directory(template_library_path, new_template_library_path)

    version = get_most_recent_git_tag()

    for dname, _, files in os.walk(new_template_library_path):
        for fname in files:
            fpath = os.path.join(dname, fname)
            with open(fpath) as f:
                s = f.read()
            s = s.replace('{{LIBRARY_NAME}}', name)
            s = s.replace('{{VERSION}}', version)
            with open(fpath, 'w') as f:
                f.write(s)

            new_fname = fname.replace('.tmpl', '')
            new_fpath = os.path.join(dname, new_fname)
            shutil.move(fpath, new_fpath)
            print('Created {path}'.format(path=new_fpath))

        new_dname = dname.replace('library-tmpl', name)
        shutil.move(dname, new_dname)

    print('Library created at {path}'.format(path=new_template_library_path))


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
