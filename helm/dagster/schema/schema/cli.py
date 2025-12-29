import json
import os
import re
import subprocess
from typing import Any

import click

from schema.charts.dagster.values import DagsterHelmValues
from schema.charts.dagster_user_deployments.values import DagsterUserDeploymentsHelmValues
from schema.charts.utils.utils import KUBERNETES_REF_KEY


def git_repo_root():
    return subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode("utf-8").strip()


def get_kubernetes_definitions_path() -> str:
    """Get the path to the local Kubernetes definitions file."""
    return os.path.join(git_repo_root(), "helm", "dagster", "kubernetes", "_definitions.json")


def load_kubernetes_definitions() -> dict[str, Any]:
    """Load Kubernetes definitions from the local file.

    The definitions file is sourced from https://github.com/yannh/kubernetes-json-schema
    and downloaded using helm/dagster/schema/scripts/update_kubernetes_definitions.py
    """
    definitions_path = get_kubernetes_definitions_path()
    if not os.path.exists(definitions_path):
        raise click.ClickException(
            f"Kubernetes definitions file not found at {definitions_path}. "
            "Run 'python helm/dagster/schema/scripts/update_kubernetes_definitions.py' to download it."
        )
    with open(definitions_path, encoding="utf8") as f:
        return json.load(f)


def find_kubernetes_refs(schema: dict[str, Any]) -> set[str]:
    """Recursively find all Kubernetes definition references in the schema.

    Looks for the special $__kubernetes_ref key that marks kubernetes references.
    """
    refs = set()

    def _find_refs(obj: Any) -> None:
        if isinstance(obj, dict):
            if KUBERNETES_REF_KEY in obj:
                refs.add(obj[KUBERNETES_REF_KEY])
            for value in obj.values():
                _find_refs(value)
        elif isinstance(obj, list):
            for item in obj:
                _find_refs(item)

    _find_refs(schema)
    return refs


def resolve_nested_refs(
    definition: dict[str, Any], all_definitions: dict[str, Any], collected: dict[str, Any]
) -> None:
    """Recursively resolve $ref references within a definition."""

    def _resolve(obj: Any) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "$ref" and isinstance(value, str):
                    # Handle internal refs like "#/definitions/io.k8s.api.core.v1.Container"
                    match = re.match(r"#/definitions/(.+)", value)
                    if match:
                        nested_def_name = match.group(1)
                        if nested_def_name not in collected and nested_def_name in all_definitions:
                            collected[nested_def_name] = all_definitions[nested_def_name]
                            resolve_nested_refs(
                                all_definitions[nested_def_name], all_definitions, collected
                            )
                else:
                    _resolve(value)
        elif isinstance(obj, list):
            for item in obj:
                _resolve(item)

    _resolve(definition)


def convert_kubernetes_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """Convert $__kubernetes_ref placeholders to proper $ref values throughout the schema."""

    def _convert(obj: Any) -> Any:
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if key == KUBERNETES_REF_KEY:
                    # Convert placeholder to proper $ref
                    result["$ref"] = f"#/$defs/kubernetes/{value}"
                else:
                    result[key] = _convert(value)
            return result
        elif isinstance(obj, list):
            return [_convert(item) for item in obj]
        else:
            return obj

    return _convert(schema)


def embed_kubernetes_definitions(schema: dict[str, Any]) -> dict[str, Any]:
    """Embed referenced Kubernetes definitions into the schema's $defs section."""
    k8s_definitions = load_kubernetes_definitions()
    all_k8s_defs = k8s_definitions.get("definitions", {})

    # Find all kubernetes refs used in the schema
    used_refs = find_kubernetes_refs(schema)

    if not used_refs:
        # Still need to convert any placeholder refs even if no k8s defs are found
        return convert_kubernetes_refs(schema)

    # Collect the definitions we need, including nested refs
    collected_defs: dict[str, Any] = {}
    for ref_name in used_refs:
        # Handle property paths like "io.k8s.api.core.v1.PodSpec/properties/nodeSelector"
        base_def_name = ref_name.split("/")[0]
        if base_def_name in all_k8s_defs:
            collected_defs[base_def_name] = all_k8s_defs[base_def_name]
            resolve_nested_refs(all_k8s_defs[base_def_name], all_k8s_defs, collected_defs)

    # Add kubernetes definitions under $defs/kubernetes
    if "$defs" not in schema:
        schema["$defs"] = {}

    # Nest all collected definitions under "kubernetes" and update internal refs
    kubernetes_defs: dict[str, Any] = {}
    for def_name, definition in collected_defs.items():
        # Deep copy and update internal refs to point to our new location
        def_copy = json.loads(json.dumps(definition))
        kubernetes_defs[def_name] = def_copy

    schema["$defs"]["kubernetes"] = kubernetes_defs

    # Update all internal refs within kubernetes definitions to use the new path
    def update_internal_refs(obj: Any) -> Any:
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                if key == "$ref" and isinstance(value, str):
                    match = re.match(r"#/definitions/(.+)", value)
                    if match:
                        result[key] = f"#/$defs/kubernetes/{match.group(1)}"
                    else:
                        result[key] = value
                else:
                    result[key] = update_internal_refs(value)
            return result
        elif isinstance(obj, list):
            return [update_internal_refs(item) for item in obj]
        else:
            return obj

    schema["$defs"]["kubernetes"] = update_internal_refs(schema["$defs"]["kubernetes"])

    # Convert all $__kubernetes_ref placeholders to proper $ref values
    schema = convert_kubernetes_refs(schema)

    return schema


CLI_HELP = """Tools to help generate the schema file for the Dagster Helm chart.
"""


@click.group(help=CLI_HELP)
def cli():
    pass


@cli.group()
def schema():
    """Generates the `values.schema.json` file according to user specified pydantic models."""


@schema.command()
def show():
    """Displays the json schema on the console."""
    click.echo("--- Dagster Helm Values ---")
    dagster_schema = json.loads(DagsterHelmValues.schema_json())
    dagster_schema = embed_kubernetes_definitions(dagster_schema)
    click.echo(json.dumps(dagster_schema, indent=4))

    click.echo("\n\n")
    click.echo("--- Dagster User Deployment Helm Values ---")
    user_deployments_schema = json.loads(DagsterUserDeploymentsHelmValues.schema_json())
    user_deployments_schema = embed_kubernetes_definitions(user_deployments_schema)
    click.echo(json.dumps(user_deployments_schema, indent=4))


@schema.command()
def apply():
    """Saves the json schema in the Helm `values.schema.json`."""
    helm_values_path_tuples = [
        (DagsterHelmValues, os.path.join(git_repo_root(), "helm", "dagster", "values.schema.json")),
        (
            DagsterUserDeploymentsHelmValues,
            os.path.join(
                git_repo_root(),
                "helm",
                "dagster",
                "charts",
                "dagster-user-deployments",
                "values.schema.json",
            ),
        ),
    ]

    for helm_values, path in helm_values_path_tuples:
        schema = json.loads(helm_values.schema_json())
        schema = embed_kubernetes_definitions(schema)
        with open(path, "w", encoding="utf8") as f:
            json.dump(schema, f, indent=4)
            f.write("\n")


def main():
    click_cli = click.CommandCollection(sources=[cli], help=CLI_HELP)
    click_cli()


if __name__ == "__main__":
    main()
