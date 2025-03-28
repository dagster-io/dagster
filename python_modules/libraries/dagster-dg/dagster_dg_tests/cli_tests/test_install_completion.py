from unittest.mock import patch

import shellingham

from dagster_dg_tests.utils import ProxyRunner, assert_runner_result


# It's quite difficult to have a true test of whether `install_completion` is working correctly,
# because it modifies the home folder. Therefore we mock the actual installation routine here and
# just ensure that the command executes and prints the correct output.
def test_install_completion():
    shell, _ = shellingham.detect_shell()
    with ProxyRunner.test() as runner, runner.isolated_filesystem():
        with patch("typer._completion_shared.install") as mock_install:
            mock_install.return_value = shell, "/some/path"
            result = runner.invoke("--install-completion")
            if shell in ["cmd", "powershell"]:  # windows shells are not supported
                assert_runner_result(result, exit_0=False)
                assert f"Shell `{shell}` is not supported" in result.output
            else:
                assert_runner_result(result)
                assert f"{shell} completion installed in /some/path" in result.output
