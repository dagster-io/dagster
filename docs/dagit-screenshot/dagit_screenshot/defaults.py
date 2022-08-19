import os

_dir = os.path.dirname(__file__)
while not os.path.exists(os.path.join(_dir, '.git')) or os.path.dirname(_dir) == _dir:
    _dir = os.path.dirname(_dir)
_repo_root = os.path.abspath(_dir)

# Root path where captured screenshots are stored.
DEFAULT_OUTPUT_ROOT = os.path.join(_repo_root, 'docs', 'next', 'public', 'images')

# Path to a screenshot spec database.
DEFAULT_SPEC_DB = os.path.join(_repo_root, 'docs', 'screenshots')

# Root path where workspaces are defined.
DEFAULT_WORKSPACE_ROOT = _repo_root
