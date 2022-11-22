from dagster._core.host_representation import ExternalRepository
from dagster._utils import file_relative_path

from .test_repository_load import successfully_load_repository_via_cli


def test_dagster_definitions():
    cli_args = ["-f", file_relative_path(__file__, "definitions_test_cases/defs_file.py")]

    executed = {}

    def the_assert(external_repo: ExternalRepository):
        assert external_repo.name == "__repository__"
        assert len(external_repo.get_external_asset_nodes()) == 1
        executed["yes"] = True

    assert successfully_load_repository_via_cli(cli_args, the_assert)

    assert executed["yes"]
