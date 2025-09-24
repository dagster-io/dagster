"""
Helpers and templates for resource renaming / aliasing.

This module is intentionally a placeholder with templates and TODOs so
that later implementation can wire up safe rename/alias operations
for resources used by definitions in Dagster.

The functions/classes here should not change runtime behavior yet.
They raise NotImplementedError or contain TODO comments for future work.
"""
from typing import Dict, Iterable, Optional, Tuple


class ResourceRenameSpec:
    """Specification describing how a resource should be renamed or aliased.

    Fields:
      - old_name: name to replace
      - new_name: name to replace with
      - allow_alias: if True, keep both old and new names (alias); if False, move/rename
    """

    def __init__(self, old_name: str, new_name: str, allow_alias: bool = False):
        self.old_name = old_name
        self.new_name = new_name
        self.allow_alias = allow_alias

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"ResourceRenameSpec(old_name={self.old_name!r}, new_name={self.new_name!r}, "
            f"allow_alias={self.allow_alias!r})"
        )


def parse_rename_specs(specs: Iterable[Tuple[str, str, Optional[bool]]]) -> Dict[str, ResourceRenameSpec]:
    """Parse an iterable of rename spec tuples into a dict keyed by old_name.

    Each tuple is expected to be (old_name, new_name) or (old_name, new_name, allow_alias).

    TODO: validate for conflicting mappings and cycles.
    """
    mapping: Dict[str, ResourceRenameSpec] = {}
    for spec in specs:
        if len(spec) == 2:
            old_name, new_name = spec
            allow_alias = False
        elif len(spec) == 3:
            old_name, new_name, allow_alias = spec
            allow_alias = bool(allow_alias)
        else:  # pragma: no cover - validation branch
            raise ValueError("Each spec must be (old_name, new_name) or (old_name, new_name, allow_alias)")

        # TODO: add cycle/conflict detection
        mapping[old_name] = ResourceRenameSpec(old_name, new_name, allow_alias)
    return mapping


def apply_rename_to_resource_dict(
    resources: Dict[str, object],
    rename_specs: Dict[str, ResourceRenameSpec],
) -> Dict[str, object]:
    """Return a new resources dict with renames applied according to specs.

    Behavior (TBD):
      - If allow_alias is True: keep both old and new keys pointing to same object
      - If allow_alias is False: remove old key and insert new key
      - If target new_name already exists: TODO define merge/overwrite semantics

    TODO: implement real logic and unit tests.
    """
    # Defensive copy to avoid mutating input
    result = dict(resources)

    for old, spec in rename_specs.items():
        if old not in resources:
            # no-op if old resource not present
            continue

        # TODO: handle collisions, deep-copy semantics, and validation
        if spec.allow_alias:
            # TODO: consider shallow copy vs aliasing behavior
            result[spec.new_name] = resources[old]
        else:
            # move/rename
            result.pop(old, None)
            result[spec.new_name] = resources[old]

    # TODO: add logging/debug info
    return result


def detect_conflicts(rename_specs: Dict[str, ResourceRenameSpec]) -> Dict[str, str]:
    """Detect simple conflicts (two old_names mapping to same new_name, cycles).

    Returns a mapping of problematic_old_name -> description of problem.

    TODO: expand to full graph cycle detection and provide actionable messages.
    """
    problems: Dict[str, str] = {}
    reverse_map: Dict[str, list] = {}
    for old, spec in rename_specs.items():
        reverse_map.setdefault(spec.new_name, []).append(old)

    for new_name, olds in reverse_map.items():
        if len(olds) > 1:
            problems[new_name] = f"Multiple sources {olds} map to same target {new_name}"

    # TODO: detect cycles (old->new->...->old)
    return problems


# Exposed API surface (currently inert)
__all__ = [
    "ResourceRenameSpec",
    "parse_rename_specs",
    "apply_rename_to_resource_dict",
    "detect_conflicts",
]
