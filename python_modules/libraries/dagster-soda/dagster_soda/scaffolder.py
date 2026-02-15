"""Scaffolder for SodaScanComponent."""

from dagster.components.component.component_scaffolder import Scaffolder
from dagster.components.component_scaffolding import scaffold_component
from dagster.components.scaffold.scaffold import ScaffoldRequest

CHECKS_YAML_TEMPLATE = """# SodaCL checks for your datasets
# See https://docs.soda.io/soda-cl/soda-cl-overview.html for SodaCL syntax
#
# Replace "my_table" with your actual dataset/table name.
# Add asset_key_map in defs.yaml to map Soda dataset names to Dagster AssetKeys.

checks for my_table:
  - row_count > 0
  # - freshness(updated_at) < 1d
  # - schema:
  #     fail:
  #       when required column missing: [id, name]
"""


class SodaScanComponentScaffolder(Scaffolder):
    """Scaffolder that generates defs.yaml and template checks.yml for SodaScanComponent."""

    def scaffold(self, request: ScaffoldRequest) -> None:
        # Compute relative path for checks.yml from project root
        checks_relative_path = "checks.yml"
        if request.project_root and request.target_path.is_relative_to(request.project_root):
            checks_relative_path = str(
                (request.target_path / "checks.yml").relative_to(request.project_root)
            ).replace("\\", "/")

        scaffold_component(
            request,
            {
                "checks_paths": [checks_relative_path],
                "configuration_path": "configuration.yml",
                "data_source_name": "my_datasource",
                "asset_key_map": {"my_table": "my_table"},
            },
        )

        checks_path = request.target_path / "checks.yml"
        checks_path.write_text(CHECKS_YAML_TEMPLATE)
