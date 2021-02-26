import yaml
from dagster.cli.workspace.config_schema import process_workspace_config
from dagster.core.test_utils import environ


def _validate_yaml_contents(yaml_contents):
    return process_workspace_config(yaml.safe_load(yaml_contents))


def test_python_file():
    terse_workspace_yaml = """
load_from:
    - python_file: a_file.py
"""

    assert _validate_yaml_contents(terse_workspace_yaml).success

    nested_workspace_yaml = """
load_from:
    - python_file:
        relative_path: a_file.py
"""

    assert _validate_yaml_contents(nested_workspace_yaml).success

    nested_workspace_yaml_with_def_name = """
load_from:
    - python_file:
        relative_path: a_file.py
        attribute: repo_symbol
"""
    assert _validate_yaml_contents(nested_workspace_yaml_with_def_name).success

    nested_workspace_yaml_with_def_name_and_location = """
load_from:
    - python_file:
        relative_path: a_file.py
        attribute: repo_symbol
        location_name: some_location
"""
    assert _validate_yaml_contents(nested_workspace_yaml_with_def_name_and_location).success

    workspace_yaml_with_executable_path = """
load_from:
    - python_file:
        relative_path: a_file.py
        executable_path: /path/to/venv/bin/python
"""
    assert _validate_yaml_contents(workspace_yaml_with_executable_path).success


def test_python_module():
    terse_workspace_yaml = """
load_from:
    - python_module: a_module
"""

    assert _validate_yaml_contents(terse_workspace_yaml).success

    nested_workspace_yaml = """
load_from:
    - python_module:
        module_name: a_module
"""

    assert _validate_yaml_contents(nested_workspace_yaml).success

    nested_workspace_yaml_with_def_name = """
load_from:
    - python_module:
        module_name: a_module
        attribute: repo_symbol
"""
    assert _validate_yaml_contents(nested_workspace_yaml_with_def_name).success

    nested_workspace_yaml_with_def_name_and_location = """
load_from:
    - python_module:
        module_name: a_module
        attribute: repo_symbol
        location_name: some_location
"""
    assert _validate_yaml_contents(nested_workspace_yaml_with_def_name_and_location).success

    workspace_yaml_with_executable_path = """
load_from:
    - python_module:
        module_name: a_module
        executable_path: /path/to/venv/bin/python
"""

    assert _validate_yaml_contents(workspace_yaml_with_executable_path).success


def test_python_package():
    workspace_yaml = """
load_from:
    - python_package: a_package
"""

    assert _validate_yaml_contents(workspace_yaml).success

    nested_workspace_yaml = """
load_from:
    - python_package:
        package_name: a_package
"""

    assert _validate_yaml_contents(nested_workspace_yaml).success

    workspace_yaml_with_executable_path = """
load_from:
    - python_package:
        package_name: a_package
        executable_path: /path/to/venv/bin/python
"""

    assert _validate_yaml_contents(workspace_yaml_with_executable_path).success


def test_cannot_do_both():
    both_yaml = """
load_from:
    - python_module: a_module
      python_file: a_file.py
"""
    assert not _validate_yaml_contents(both_yaml).success


def test_load_both():
    both_yaml = """
load_from:
    - python_module: a_module
    - python_file: a_file.py
"""

    assert _validate_yaml_contents(both_yaml).success


def test_load_python_environment_with_file():
    python_environment_yaml_with_file = """
load_from:
    - python_environment:
        executable_path: /path/to/venv/bin/python
        target:
            python_file: file_valid_in_that_env.py
"""

    validation_result = _validate_yaml_contents(python_environment_yaml_with_file)

    assert validation_result.success


def test_load_python_environment_with_module():
    python_environment_yaml_with_module = """
load_from:
    - python_environment:
        executable_path: /path/to/venv/bin/python
        target:
            python_module: module_valid_in_that_env.py
"""

    validation_result = _validate_yaml_contents(python_environment_yaml_with_module)

    assert validation_result.success


def test_load_python_environment_with_env_var():
    with environ({"TEST_EXECUTABLE_PATH": "executable/path/bin/python"}):
        python_environment_yaml_with_file = """
    load_from:
        - python_environment:
            executable_path:
                env: TEST_EXECUTABLE_PATH
            target:
                python_file: file_valid_in_that_env.py
    """

        validation_result = _validate_yaml_contents(python_environment_yaml_with_file)

        assert validation_result.success


def test_load_python_file_with_env_var():
    with environ({"TEST_EXECUTABLE_PATH": "executable/path/bin/python"}):
        workspace_yaml = """
    load_from:
        - python_file:
            relative_path: file_valid_in_that_env.py
            executable_path:
                env: TEST_EXECUTABLE_PATH
    """

        validation_result = _validate_yaml_contents(workspace_yaml)

        assert validation_result.success


def test_load_python_module_with_env_var():
    with environ({"TEST_EXECUTABLE_PATH": "executable/path/bin/python"}):
        workspace_yaml = """
    load_from:
        - python_module:
            module_name: module_valid_in_that_env
            executable_path:
                env: TEST_EXECUTABLE_PATH
    """

        validation_result = _validate_yaml_contents(workspace_yaml)

        assert validation_result.success


def test_load_python_package_with_env_var():
    with environ({"TEST_EXECUTABLE_PATH": "executable/path/bin/python"}):
        workspace_yaml = """
    load_from:
        - python_package:
            package_name: package_valid_in_that_env
            executable_path:
                env: TEST_EXECUTABLE_PATH
    """

        validation_result = _validate_yaml_contents(workspace_yaml)

        assert validation_result.success


def test_load_from_grpc_server():
    with environ({"TEST_EXECUTABLE_PATH": "executable/path/bin/python"}):
        valid_yaml = """
    load_from:
        - grpc_server:
            host: remotehost
            port: 4266
            location_name: 'my_grpc_server'
    """

        validation_result = _validate_yaml_contents(valid_yaml)

        assert validation_result.success


def test_load_from_grpc_server_env():
    with environ(
        {
            "TEST_EXECUTABLE_PATH": "executable/path/bin/python",
            "FOO_PORT": "1234",
            "FOO_SOCKET": "barsocket",
            "FOO_HOST": "barhost",
        }
    ):
        valid_yaml = """
    load_from:
        - grpc_server:
            host:
              env: FOO_HOST
            port:
              env: FOO_PORT
            location_name: 'my_grpc_server'
    """

        validation_result = _validate_yaml_contents(valid_yaml)

        valid_socket_yaml = """
    load_from:
        - grpc_server:
            host:
              env: FOO_HOST
            socket:
              env: FOO_SOCKET
            location_name: 'my_grpc_server'
    """

        validation_result = _validate_yaml_contents(valid_socket_yaml)

        assert validation_result.success


def test_load_python_environment_and_grpc_server():
    with environ({"TEST_EXECUTABLE_PATH": "executable/path/bin/python"}):
        valid_yaml = """
    load_from:
        - grpc_server:
            host: remotehost
            port: 4266
            location_name: 'my_grpc_server'
        - python_environment:
            executable_path:
                env: TEST_EXECUTABLE_PATH
            target:
                python_file: file_valid_in_that_env.py
    """

        validation_result = _validate_yaml_contents(valid_yaml)

        assert validation_result.success
