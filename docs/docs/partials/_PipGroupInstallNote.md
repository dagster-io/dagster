:::note

`pip install --group` requires pip 25.1 or later (April 2025). It reads dependencies from `[dependency-groups.dev]` in your `pyproject.toml` — projects created with `create-dagster project` already declare the relevant packages there. If your project does not use PEP 735 dependency groups, install the packages directly instead (e.g. `pip install dagster-dg-cli`). For more information, see [PEP 735](https://peps.python.org/pep-0735/).

:::
