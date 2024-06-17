from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Type, Union, cast

import github3
from dagster import (
    Definitions,
)
from dagster import (
    _check as check,
)
from dagster._config.pythonic_config.type_check_utils import safe_is_subclass
from dagster._model.pydantic_compat_layer import json_schema_from_type
from dagster._utils.pydantic_yaml import (
    parse_yaml_file_to_pydantic,
    parse_yaml_file_to_pydantic_sequence,
)
from typing_extensions import get_args, get_origin

from .blueprint import Blueprint, BlueprintDefinitions
from .blueprint_manager import BlueprintManager, attach_code_references_to_definitions


def _attach_blob_to_blueprint(blueprint: Blueprint, blob: str) -> Blueprint:
    object.__setattr__(blueprint, "_blob", blob)
    return blueprint


def load_blueprints_from_yaml(
    *,
    path: Union[Path, str],
    per_file_blueprint_type: Union[Type[Blueprint], Type[Sequence[Blueprint]]],
) -> Sequence[Blueprint]:
    """Load blueprints from a YAML file or directory of YAML files.

    Args:
        path (Path | str): The path to the YAML file or directory of YAML files containing the
            blueprints for Dagster definitions.
        per_file_blueprint_type (Union[Type[Blueprint], Sequence[Type[Blueprint]]]): The type
            of blueprint that each of the YAML files are expected to conform to. If a sequence
            type is provided, the function will expect each YAML file to contain a list of
            blueprints.

    Returns:
        Sequence[Blueprint]: The loaded blueprints.
    """
    resolved_path = Path(path)
    check.invariant(
        resolved_path.exists(), f"No file or directory at path: {resolved_path}"
    )
    file_paths: list[Path]
    if resolved_path.is_file():
        file_paths = [resolved_path]
    else:
        file_paths = list(resolved_path.rglob("*.yaml")) + list(
            resolved_path.rglob("*.yml")
        )

    origin = get_origin(per_file_blueprint_type)
    if safe_is_subclass(origin, Sequence):
        args = get_args(per_file_blueprint_type)
        check.invariant(
            args and len(args) == 1,
            "Sequence type annotation must have a single Blueprint type argument",
        )

        # flatten the list of blueprints from all files
        blueprints = [
            _attach_blob_to_blue
            for file_path in file_paths
            for blueprint in parse_yaml_file_to_pydantic_sequence(
                args[0], file_path.read_text(), str(file_path)
            )
        ]

    else:
        blueprints = [
            _attach_blob_to_blueprint(
                parse_yaml_file_to_pydantic(
                    cast(Type[Blueprint], per_file_blueprint_type),
                    file_path.read_text(),
                    str(file_path),
                ),
                file_path.read_text(),
            )
            for file_path in file_paths
        ]

    return blueprints


def load_defs_from_yaml(
    *,
    path: Union[Path, str],
    per_file_blueprint_type: Union[Type[Blueprint], Type[Sequence[Blueprint]]],
    resources: Optional[Dict[str, Any]] = None,
) -> Definitions:
    """Load Dagster definitions from a YAML file of blueprints.

    Args:
        path (Path | str): The path to the YAML file or directory of YAML files containing the
            blueprints for Dagster definitions.
        per_file_blueprint_type (Union[Type[Blueprint], Sequence[Type[Blueprint]]]): The type
            of blueprint that each of the YAML files are expected to conform to. If a sequence
            type is provided, the function will expect each YAML file to contain a list of
            blueprints.
        resources (Dict[str, Any], optional): A dictionary of resources to be bound to the
            definitions. Defaults to None.

    Returns:
        Definitions: The loaded Dagster Definitions object.
    """
    blueprints = load_blueprints_from_yaml(
        path=path, per_file_blueprint_type=per_file_blueprint_type
    )

    def_sets_with_code_references = [
        attach_code_references_to_definitions(
            blueprint, blueprint.build_defs_add_context_to_errors()
        )
        for blueprint in blueprints
    ]

    return BlueprintDefinitions.merge(
        *def_sets_with_code_references, BlueprintDefinitions(resources=resources or {})
    ).to_definitions()


@dataclass(frozen=True)
class YamlBlueprintsLoader(BlueprintManager):
    """A loader is responsible for loading a set of Dagster definitions from one or more YAML
    files based on a set of supplied blueprints.
    """

    path: Path
    per_file_blueprint_type: Union[Type[Blueprint], Type[Sequence[Blueprint]]]
    name: Optional[str] = None

    def get_name(self) -> str:
        return self.name or self.path.name

    def load_blueprints(self) -> Sequence[Blueprint]:
        return load_blueprints_from_yaml(
            path=self.path, per_file_blueprint_type=self.per_file_blueprint_type
        )

    def model_json_schema(self) -> Dict[str, Any]:
        """Returns a JSON schema for the model or models that the loader is responsible for loading."""
        return json_schema_from_type(self.per_file_blueprint_type)

    def add_blueprint(self, identifier: object, blob: str) -> str:
        user_access_token = "xxx"
        gh = github3.GitHub(token=user_access_token)
        repo = gh.repository("benpankow", "blueprint-ui-demo")

        import uuid

        branch_name: str = f"test-{uuid.uuid4().hex[:7]}"
        repo.create_branch_ref(branch_name, repo.branch(repo.default_branch).commit)

        repo_path = identifier
        blob = repo.create_blob(content=blob, encoding="utf-8")
        tree_content = []
        tree_content.append(
            {"path": repo_path, "mode": "100644", "type": "blob", "sha": blob}
        )

        branch = repo.branch(branch_name)
        tree = repo.create_tree(tree_content, branch.commit.commit.tree.sha)
        commit = repo.create_commit(
            message="Add Dagster Cloud deploy actions",
            tree=tree.sha,
            parents=[branch.commit.sha],
        )
        ref = repo.ref(f"heads/{branch_name}")
        ref.update(commit.sha)

        pull_request = repo.create_pull(
            f"Add {identifier} blueprint",
            base=repo.default_branch,
            head=branch_name,
            body=(
                "This is an automated pull request created by Dagster+ on behalf of the user "
                "to add a new blueprint to the repository."
            ),
        )
        return pull_request.html_url

    def update_blueprint(self, identifier: object, blob: str) -> str:
        user_access_token = "xxx"
        gh = github3.GitHub(token=user_access_token)
        repo = gh.repository("benpankow", "blueprint-ui-demo")

        import uuid

        branch_name: str = f"test-{uuid.uuid4().hex[:7]}"
        repo.create_branch_ref(branch_name, repo.branch(repo.default_branch).commit)

        repo_path = identifier
        blob = repo.create_blob(content=blob, encoding="utf-8")
        tree_content = []
        tree_content.append(
            {"path": repo_path, "mode": "100644", "type": "blob", "sha": blob}
        )

        branch = repo.branch(branch_name)
        tree = repo.create_tree(tree_content, branch.commit.commit.tree.sha)
        commit = repo.create_commit(
            message="Add Dagster Cloud deploy actions",
            tree=tree.sha,
            parents=[branch.commit.sha],
        )
        ref = repo.ref(f"heads/{branch_name}")
        ref.update(commit.sha)

        pull_request = repo.create_pull(
            f"Add {identifier} blueprint",
            base=repo.default_branch,
            head=branch_name,
            body=(
                "This is an automated pull request created by Dagster+ on behalf of the user "
                "to add a new blueprint to the repository."
            ),
        )
        return pull_request.html_url
