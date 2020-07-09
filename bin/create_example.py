#!/usr/bin/env python3

"""
To use, run
 python bin/create_example.py --name example_name
"""
from __future__ import absolute_import

import json
import os
import shutil

import click
from automation.git import get_most_recent_git_tag

EXAMPLES_JSON_PATH = 'docs/next/src/pages/examples/examples.json'


def copy_directory(src, dest):
    try:
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns('.DS_Store'))
    # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
    # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)


def add_to_examples_json(name):
    with open(EXAMPLES_JSON_PATH, 'r') as examples_file:
        examples = json.load(examples_file)

    if name in {example['name'] for example in examples}:
        raise click.UsageError(
            'Example with name {name} already exists in {path}'.format(
                name=name, path=EXAMPLES_JSON_PATH
            )
        )

    examples.append({'name': name, 'title': '', 'description': ''})

    with open(EXAMPLES_JSON_PATH, 'w') as examples_file:
        json.dump(examples, examples_file, indent=4)


@click.command()
@click.option('--name', prompt='Name of example to create', help='Name of example')
def main(name):
    template_library_path = os.path.abspath('bin/assets/dagster-example-tmpl')
    new_template_library_path = os.path.abspath('examples/{name}'.format(name=name))
    doc_path = os.path.abspath('./docs/next/src/pages/examples/{name}.mdx'.format(name=name))

    if os.path.exists(new_template_library_path):
        raise click.UsageError('Example with name {name} already exists'.format(name=name))

    if os.path.exists(doc_path):
        raise click.UsageError('Docs page already exists: {doc_path}'.format(doc_path=doc_path))

    add_to_examples_json(name)

    copy_directory(template_library_path, new_template_library_path)

    version = get_most_recent_git_tag()

    for dname, _, files in os.walk(new_template_library_path):
        for fname in files:
            fpath = os.path.join(dname, fname)
            with open(fpath) as f:
                s = f.read()
            s = s.replace('{{EXAMPLE_NAME}}', name)
            s = s.replace('{{VERSION}}', version)
            with open(fpath, 'w') as f:
                f.write(s)

            new_fname = fname.replace('.tmpl', '').replace('{{EXAMPLE_NAME}}', name)
            new_fpath = os.path.join(dname, new_fname)
            shutil.move(fpath, new_fpath)
            print('Created {path}'.format(path=new_fpath))

        new_dname = dname.replace('example-tmpl', name)
        shutil.move(dname, new_dname)

    shutil.move(os.path.join(new_template_library_path, 'README.mdx'), doc_path)

    print('Example created at {path}'.format(path=new_template_library_path))
    print('Documentation stub created at {path}'.format(path=doc_path))
    print('Added metadata to {path}'.format(path=EXAMPLES_JSON_PATH))


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
