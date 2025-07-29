"""Tests for path converter functions."""

from pathlib import Path

from automation.dagster_docs.path_converters import (
    dagster_path_converter,
    generic_path_converter,
    simple_package_converter,
)


class TestDagsterPathConverter:
    def test_core_dagster_module(self):
        root = Path("/dagster")
        file_path = root / "python_modules" / "dagster" / "dagster" / "core" / "executor.py"

        result = dagster_path_converter(file_path, root)
        assert result == "dagster.core.executor"

    def test_core_dagster_init_module(self):
        root = Path("/dagster")
        file_path = root / "python_modules" / "dagster" / "dagster" / "core" / "__init__.py"

        result = dagster_path_converter(file_path, root)
        assert result == "dagster.core"

    def test_library_module(self):
        root = Path("/dagster")
        file_path = root / "python_modules" / "libraries" / "dagster-aws" / "dagster_aws" / "s3.py"

        result = dagster_path_converter(file_path, root)
        assert result == "dagster_aws.dagster_aws.s3"

    def test_library_init_module(self):
        root = Path("/dagster")
        file_path = (
            root
            / "python_modules"
            / "libraries"
            / "dagster-snowflake"
            / "dagster_snowflake"
            / "__init__.py"
        )

        result = dagster_path_converter(file_path, root)
        assert result == "dagster_snowflake.dagster_snowflake"

    def test_non_python_modules_path(self):
        root = Path("/dagster")
        file_path = root / "docs" / "content" / "example.py"

        result = dagster_path_converter(file_path, root)
        assert result is None

    def test_invalid_library_structure(self):
        root = Path("/dagster")
        file_path = root / "python_modules" / "libraries" / "incomplete.py"

        result = dagster_path_converter(file_path, root)
        assert result == "incomplete"

    def test_unknown_python_modules_structure(self):
        root = Path("/dagster")
        file_path = root / "python_modules" / "unknown" / "module.py"

        result = dagster_path_converter(file_path, root)
        assert result is None

    def test_file_outside_root(self):
        root = Path("/dagster")
        file_path = Path("/other") / "module.py"

        result = dagster_path_converter(file_path, root)
        assert result is None


class TestGenericPathConverter:
    def test_simple_module(self):
        root = Path("/project")
        file_path = root / "mypackage" / "module.py"

        result = generic_path_converter(file_path, root)
        assert result == "mypackage.module"

    def test_nested_module(self):
        root = Path("/project")
        file_path = root / "mypackage" / "subpackage" / "module.py"

        result = generic_path_converter(file_path, root)
        assert result == "mypackage.subpackage.module"

    def test_init_module(self):
        root = Path("/project")
        file_path = root / "mypackage" / "__init__.py"

        result = generic_path_converter(file_path, root)
        assert result == "mypackage"

    def test_root_level_module(self):
        root = Path("/project")
        file_path = root / "module.py"

        result = generic_path_converter(file_path, root)
        assert result == "module"

    def test_root_level_init(self):
        root = Path("/project")
        file_path = root / "__init__.py"

        result = generic_path_converter(file_path, root)
        assert result is None

    def test_file_outside_root(self):
        root = Path("/project")
        file_path = Path("/other") / "module.py"

        result = generic_path_converter(file_path, root)
        assert result is None

    def test_non_python_file(self):
        root = Path("/project")
        file_path = root / "mypackage" / "data.txt"

        # Should still work, just without .py extension handling
        result = generic_path_converter(file_path, root)
        assert result == "mypackage.data.txt"


class TestSimplePackageConverter:
    def test_create_converter(self):
        converter = simple_package_converter("mypackage")

        root = Path("/project")
        file_path = root / "submodule.py"

        result = converter(file_path, root)
        assert result == "mypackage.submodule"

    def test_nested_modules(self):
        converter = simple_package_converter("mypackage")

        root = Path("/project")
        file_path = root / "sub1" / "sub2" / "module.py"

        result = converter(file_path, root)
        assert result == "mypackage.sub1.sub2.module"

    def test_init_module(self):
        converter = simple_package_converter("mypackage")

        root = Path("/project")
        file_path = root / "subpackage" / "__init__.py"

        result = converter(file_path, root)
        assert result == "mypackage.subpackage"

    def test_root_level_module(self):
        converter = simple_package_converter("mypackage")

        root = Path("/project")
        file_path = root / "module.py"

        result = converter(file_path, root)
        assert result == "mypackage.module"

    def test_root_level_init(self):
        converter = simple_package_converter("mypackage")

        root = Path("/project")
        file_path = root / "__init__.py"

        result = converter(file_path, root)
        assert result == "mypackage"

    def test_file_outside_root(self):
        converter = simple_package_converter("mypackage")

        root = Path("/project")
        file_path = Path("/other") / "module.py"

        result = converter(file_path, root)
        assert result is None
