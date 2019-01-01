import os
import subprocess
import tempfile


def test_build_all_docs():
    build_dir = tempfile.mkdtemp()
    cmds = [
        'sphinx-build',
        '-b',
        'html',
        '-d',
        os.path.join(build_dir, 'doctrees'),
        '.',
        os.path.join(build_dir, 'html'),
    ]
    subprocess.check_output(cmds)
