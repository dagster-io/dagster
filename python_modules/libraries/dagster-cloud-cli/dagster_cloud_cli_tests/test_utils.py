from unittest.mock import patch

from dagster_cloud_cli.core.pex_builder.code_location import get_local_repo_name


def testget_local_repo_name():
    def mock_check_output(args):
        return "git@github.com:org/repo.git"

    with patch("subprocess.check_output", return_value=b"git@github.com:org/repo.git"):
        assert get_local_repo_name(".") == "org/repo"

    with patch("subprocess.check_output", return_value=b"https://github.com/org/repo.git"):
        assert get_local_repo_name(".") == "org/repo"
