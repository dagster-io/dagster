from collections.abc import Sequence
from pathlib import Path

from dagster import PipesSubprocessClient
from dagster_blueprints import YamlBlueprintsLoader
from dagster_blueprints.shell_command_blueprint import ShellCommandBlueprint

blueprints_path = Path(__file__).parent / "pipelines"

loader = YamlBlueprintsLoader(
    per_file_blueprint_type=Sequence[ShellCommandBlueprint], path=blueprints_path
)
defs = loader.load_defs(
    resources={"pipes_subprocess_client": PipesSubprocessClient(cwd=str(blueprints_path))},
)
