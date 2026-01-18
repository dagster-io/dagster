import os
import sys
from collections.abc import Mapping
from typing import Optional

import dagster as dg
import pytest
from dagster._core.code_pointer import CodePointer
from dagster._core.remote_origin import InProcessCodeLocationOrigin
from dagster._core.remote_representation.code_location import InProcessCodeLocation
from dagster._core.test_utils import instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin


class InProcesssCodeLocationWithoutCodePointers(InProcessCodeLocation):
    @property
    def repository_code_pointer_dict(self) -> Mapping[str, Optional[CodePointer]]:
        return {}


@dg.asset
def my_asset():
    pass


defs = dg.Definitions(assets=[my_asset])


def test_repo_handle_without_code_pointers():
    origin = InProcessCodeLocationOrigin(
        loadable_target_origin=LoadableTargetOrigin(
            executable_path=sys.executable,
            python_file=__file__,
            working_directory=os.path.dirname(__file__),
            attribute=None,
        ),
        container_image=None,
        entry_point=None,
        container_context=None,
        location_name=None,
    )

    with instance_for_test() as instance:
        location = InProcesssCodeLocationWithoutCodePointers(origin=origin, instance=instance)

        assert location.repository_code_pointer_dict == {}

        assert len(location.get_repositories()) == 1

        repo = next(iter(location.get_repositories().values()))
        assert repo.handle is not None
        assert repo.handle.repository_python_origin is None

        with pytest.raises(Exception, match="Repository does not have a RepositoryPythonOrigin"):
            repo.handle.get_python_origin()

        job = next(iter(repo.get_all_jobs()))
        assert job.handle is not None

        assert job.handle.get_remote_origin() is not None
        with pytest.raises(Exception, match="Repository does not have a RepositoryPythonOrigin"):
            job.handle.get_python_origin()
