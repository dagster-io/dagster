import pathlib
import shutil

import sphinx
import pytest

# this is necessary because Sphinx isn't exposing its fixtures
# https://docs.pytest.org/en/7.1.x/how-to/writing_plugins.html#requiring-loading-plugins-in-a-test-module-or-conftest-file
pytest_plugins = ['sphinx.testing.fixtures']


# TODO: Remove when we no longer care about Sphinx < 7.2
@pytest.fixture
def rootdir(tmpdir):
    if sphinx.version_info >= (7, 2, 0):
        src = pathlib.Path(__file__).parent.absolute().joinpath('roots')
        dst = tmpdir.join('roots')
        shutil.copytree(src, dst)
        roots = pathlib.Path(dst)
    else:
        from sphinx.testing import path

        src = path.path(__file__).parent.abspath() / 'roots'
        dst = tmpdir.join('roots')
        shutil.copytree(src, dst)
        roots = path.path(dst)

    yield roots
    shutil.rmtree(dst)
