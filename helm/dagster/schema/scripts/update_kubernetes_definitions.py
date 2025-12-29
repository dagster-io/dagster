#!/usr/bin/env python3
"""Script to download Kubernetes JSON Schema definitions for use in Helm chart validation.

The definitions are sourced from https://github.com/yannh/kubernetes-json-schema
which is an actively maintained fork of the original instrumenta/kubernetes-json-schema.

This script downloads the _definitions.json file for a specified Kubernetes version
and stores it locally so the Helm chart schema can work in air-gapped environments
without requiring external network access.

Usage:
    python update_kubernetes_definitions.py [--version VERSION]

Example:
    python update_kubernetes_definitions.py --version 1.19.0
"""

import argparse
import json
import os
import subprocess
import urllib.request
from datetime import datetime, timezone

# Default Kubernetes version to download
DEFAULT_VERSION = "1.19.0"

# Source repository for Kubernetes JSON schemas
SOURCE_REPO = "https://github.com/yannh/kubernetes-json-schema"
SOURCE_URL_TEMPLATE = "https://raw.githubusercontent.com/yannh/kubernetes-json-schema/master/v{version}/_definitions.json"


def git_repo_root() -> str:
    return subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode("utf-8").strip()


def get_output_path() -> str:
    """Get the path where the definitions file should be saved."""
    return os.path.join(git_repo_root(), "helm", "dagster", "kubernetes", "_definitions.json")


def download_definitions(version: str) -> dict:
    """Download the Kubernetes definitions for the specified version."""
    url = SOURCE_URL_TEMPLATE.format(version=version)
    print(f"Downloading Kubernetes {version} definitions from:\n  {url}")  # noqa: T201

    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


def add_attribution(definitions: dict, version: str) -> dict:
    """Add attribution metadata to the definitions."""
    definitions["$comment"] = (
        f"Kubernetes {version} JSON Schema definitions. "
        f"Source: {SOURCE_REPO} (Apache-2.0 License). "
        f"Downloaded: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}. "
        "Do not edit manually - regenerate using helm/dagster/schema/scripts/update_kubernetes_definitions.py"
    )
    return definitions


def main():
    parser = argparse.ArgumentParser(
        description="Download Kubernetes JSON Schema definitions for Helm chart validation."
    )
    parser.add_argument(
        "--version",
        default=DEFAULT_VERSION,
        help=f"Kubernetes version to download (default: {DEFAULT_VERSION})",
    )
    args = parser.parse_args()

    # Download definitions
    definitions = download_definitions(args.version)

    # Add attribution
    definitions = add_attribution(definitions, args.version)

    # Ensure output directory exists
    output_path = get_output_path()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write definitions to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(definitions, f, indent=2)
        f.write("\n")

    print(f"Saved definitions to:\n  {output_path}")  # noqa: T201
    print(  # noqa: T201
        f"\nDefinitions contain {len(definitions.get('definitions', {}))} Kubernetes object schemas."
    )


if __name__ == "__main__":
    main()
