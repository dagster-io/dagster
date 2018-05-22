import os


def main(argv):
    script = argv[0]
    target_dir = argv[1]
    script_dir = os.path.dirname(script)
    template_dir = os.path.join(script_dir, '../template')
    os.system(f'cp -r {template_dir} {target_dir}')
    source_dir = target_dir.replace('-', '_')
    os.system(f'mkdir {target_dir}/{source_dir}')
    init_header = \
'''from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import *  # pylint: disable=W0622,W0401
'''

    with open(f'{target_dir}/{source_dir}/__init__.py', 'w') as f:
        f.write(init_header)
    os.system(f'mkdir {target_dir}/{source_dir}_tests')
    os.system(f'touch {target_dir}/{source_dir}_tests/__init__.py')
    print(template_dir)
    print(argv)
