import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import click

from dagster_dg.utils import is_macos, is_windows


def get_default_extension_dir() -> Path:
    if is_windows():
        return Path.home() / "AppData" / "dg" / "vscode"
    elif is_macos():
        return Path.home() / "Library" / "Application Support" / "dg" / "vscode"
    else:
        return Path.home() / ".local" / "share" / "dg" / "vscode"


def has_editor_cli_command(executable_name: str) -> bool:
    return bool(shutil.which(executable_name))


def run_editor_cli_command(executable_name: str, args: list[str]) -> bytes:
    return subprocess.check_output([executable_name] + args)


def recommend_yaml_extension(executable_name: str) -> None:
    if not has_editor_cli_command(executable_name):
        raise click.ClickException(
            f"Could not find `{executable_name}` executable in PATH. In order to use the dagster-components-schema extension, "
            "please install the redhat.vscode-yaml extension manually."
        )

    extensions = (
        run_editor_cli_command(executable_name, ["--list-extensions"]).decode("utf-8").split("\n")
    )
    if "redhat.vscode-yaml" in extensions:
        click.echo("redhat.vscode-yaml extension is already installed.")
    else:
        if click.confirm(
            "The redhat.vscode-yaml extension is not installed. Would you like to install it now?"
        ):
            run_editor_cli_command(executable_name, ["--install-extension", "redhat.vscode-yaml"])


def install_or_update_yaml_schema_extension(
    executable_name: str, yaml_dir: Path, schema_path: Path
) -> None:
    """Builds a VS Code extension which associates the built JSON schema files with YAML
    files in the provided directory, provided that the user has the Red Hat YAML extension
    already installed.
    """
    extension_working_dir = get_default_extension_dir() / "dagster-components-schema"
    extension_package_json_path = extension_working_dir / "package.json"

    template_package_json_path = Path(__file__).parent / "vscode_extension_package.json"
    template_package_json = json.loads(template_package_json_path.read_text())
    template_package_json["contributes"]["yamlValidation"] = [
        {"fileMatch": f"{yaml_dir}/**/*.y*ml", "url": f"{schema_path}"}
    ]

    extension_working_dir.mkdir(parents=True, exist_ok=True)

    # Merge with existing yamlValidation entries, so we can provide schema completions for many
    # projects.
    if extension_package_json_path.exists():
        existing_package_json = json.loads(extension_package_json_path.read_text())
        existing_yaml_validation = existing_package_json["contributes"].get("yamlValidation")
        if existing_yaml_validation:
            template_package_json["contributes"]["yamlValidation"].extend(
                entry
                for entry in existing_yaml_validation
                if entry["fileMatch"] != f"{yaml_dir}/**/*.y*ml"
            )

    extension_package_json_path.write_text(json.dumps(template_package_json, indent=2))
    click.echo(f"Set up package.json for VS Code extension in {extension_package_json_path}")

    # Local VS Code extensions must be packaged into a vsix file, which under the hood is just a zip file
    # with a special extension.
    extension_zip_path = extension_working_dir / "dagster-components-schema.vsix"
    with zipfile.ZipFile(extension_zip_path, "w") as z:
        z.write(extension_package_json_path, "extension/package.json")

    click.echo(f"Packaged extension to {extension_zip_path}")

    try:
        run_editor_cli_command(
            executable_name, ["--uninstall-extension", "dagster.dagster-components-schema"]
        )
    except subprocess.CalledProcessError:
        click.echo("No existing dagster.dagster-components-schema extension to uninstall.")
    run_editor_cli_command(
        executable_name, ["--install-extension", os.fspath(extension_zip_path.resolve())]
    )
    click.echo("Successfully installed Dagster Components schema extension.")
