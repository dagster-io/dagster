import sys
from pathlib import Path

import pytest
from dagster_dg_cli.cli.plus.integrations.dbt import _discover_dbt_projects

# dbt-core does not support Python 3.14: importing it pulls in dbt_common, whose
# module-level mashumaro schema build fails on 3.14's union types.
pytestmark = pytest.mark.skipif(
    sys.version_info >= (3, 14), reason="dbt-core does not support Python 3.14"
)


def test_discover_dbt_projects_from_file_named_dbt(tmp_path: Path) -> None:
    """A user file named dbt.py must not be imported under the module name `dbt`.

    Doing so replaces dbt-core in sys.modules, and dbt's mashumaro-generated
    deserializers then fail with `module 'dbt' has no attribute 'contracts'`.
    """
    # deferred like the CLI's own dagster_dbt import, so collection doesn't
    # require dbt-core
    import dbt

    user_file = tmp_path / "dbt.py"
    user_file.write_text('SENTINEL = "user module"\n')

    assert _discover_dbt_projects(components_path=None, file_path=user_file) == []

    assert sys.modules["dbt"] is dbt
    assert not hasattr(dbt, "SENTINEL")
