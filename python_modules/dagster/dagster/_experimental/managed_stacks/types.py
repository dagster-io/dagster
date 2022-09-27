import enum
import itertools
from abc import abstractmethod
from typing import List, NamedTuple, Optional, OrderedDict, Tuple, Union

import click

from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition


class ManagedStackError(enum.Enum):
    CANNOT_CONNECT = "cannot_connect"


def _sanitize(key: str, value: str):
    """
    Rudamentary sanitization of values so we can avoid printing passwords
    to the console.
    """
    if "password" in key.lower() or "token" in key.lower():
        return "**********"
    return value


class ManagedStackDiff(
    NamedTuple(
        "_ManagedStackDiff",
        [
            ("additions", List[Tuple[str, str]]),
            ("deletions", List[Tuple[str, str]]),
            ("modifications", List[Tuple[str, str, str]]),
            ("nested", OrderedDict[str, "ManagedStackDiff"]),
        ],
    )
):
    """
    Utility class representing the diff between configured and deployed managed stack. Can be rendered to a
    color-coded, user-friendly string.
    """

    def __new__(
        cls,
        additions: Optional[List[Tuple[str, str]]] = None,
        deletions: Optional[List[Tuple[str, str]]] = None,
        modifications: Optional[List[Tuple[str, str, str]]] = None,
    ):
        return super().__new__(
            cls,
            additions or [],
            deletions or [],
            modifications or [],
            OrderedDict({}),
        )

    def add(self, name: str, value: str) -> "ManagedStackDiff":
        """
        Adds an addition entry to the diff.
        """
        return self._replace(additions=self.additions + [(name, value)])

    def delete(self, name: str, value: str) -> "ManagedStackDiff":
        """
        Adds a deletion entry to the diff.
        """
        return self._replace(deletions=self.deletions + [(name, value)])

    def modify(self, name: str, old_value: str, new_value: str) -> "ManagedStackDiff":
        """
        Adds a modification entry to the diff.
        """
        return self._replace(modifications=self.modifications + [(name, old_value, new_value)])

    def with_nested(self, name: str, nested: "ManagedStackDiff") -> "ManagedStackDiff":
        """
        Adds the nested diff as a child of the current diff.
        """
        return self._replace(nested=OrderedDict(list(self.nested.items()) + [(name, nested)]))

    def join(self, other: "ManagedStackDiff") -> "ManagedStackDiff":
        """
        Combines two diff objects into a single diff object.
        """
        return self._replace(
            additions=self.additions + other.additions,
            deletions=self.deletions + other.deletions,
            modifications=self.modifications + other.modifications,
            nested=OrderedDict(list(self.nested.items()) + list(other.nested.items())),
        )

    def is_empty(self):
        """
        Returns whether the diff is a no-op.
        """
        return (
            len(self.additions) == 0
            and len(self.deletions) == 0
            and len(self.modifications) == 0
            and all(nested_diff.is_empty() for nested_diff in self.nested.values())
        )

    def __str__(self):
        my_additions, my_deletions, my_modifications = self.get_diff_display_entries()
        additions_str = "\n".join(my_additions)
        deletions_str = "\n".join(my_deletions)
        modifications_str = "\n".join(my_modifications)
        return f"{additions_str}\n{deletions_str}\n{modifications_str}"

    def get_diff_display_entries(self, indent: int = 0) -> Tuple[List[str], List[str], List[str]]:
        """
        Returns a tuple of additions, deletions, and modification entries associated with this diff object.
        """

        # Get top-level additions/deletions/modifications
        my_additions = [
            click.style(f"{' ' * indent}+ {k}: {_sanitize(k, v)}", fg="green")
            for k, v in self.additions
        ]
        my_deletions = [
            click.style(f"{' ' * indent}- {k}: {_sanitize(k, v)}", fg="red")
            for k, v in self.deletions
        ]
        my_modifications = [
            click.style(
                f"{' ' * indent}~ {k}: {_sanitize(k, old_v)} -> {_sanitize(k, new_v)}", fg="yellow"
            )
            for k, old_v, new_v in self.modifications
        ]

        # Get entries for each nested diff
        for key, nested_diff in self.nested.items():
            (
                nested_additions,
                nested_deletions,
                nested_modifications,
            ) = nested_diff.get_diff_display_entries(indent + 2)

            # If there are no changes, skip this nested diff
            if (
                len(nested_additions) == 0
                and len(nested_deletions) == 0
                and len(nested_modifications) == 0
            ):
                continue
            elif len(nested_deletions) == 0 and len(nested_modifications) == 0:
                # If there are only additions, display the nested entry as an addition
                my_additions += [
                    click.style(f"{' ' * indent}+ {key}:", fg="green")
                ] + nested_additions
            elif len(nested_additions) == 0 and len(nested_modifications) == 0:
                # If there are only deletions, display the nested entry as a deletion
                my_deletions += [
                    click.style(f"{' ' * indent}- {key}:", fg="red")
                ] + nested_deletions
            else:
                # If there are only modifications, display the nested entry as a modification
                my_modifications += [
                    click.style(f"{' ' * indent}~ {key}:", fg="yellow")
                ] + nested_modifications

        return (my_additions, my_deletions, my_modifications)


"""
Union type representing the status of a managed stack - can either
return the (potentially empty) diff between the configured and deployed
stack, or an error.
"""
ManagedStackCheckResult = Union[ManagedStackDiff, ManagedStackError]


class ManagedStackAssetsDefinition(CacheableAssetsDefinition):
    def __init__(self, unique_id: str):
        super().__init__(unique_id)

    @abstractmethod
    def check(self) -> ManagedStackCheckResult:
        """
        Returns whether the user provided config for the managed stack is in sync with the external resource.
        """
        raise NotImplementedError()

    @abstractmethod
    def apply(self) -> ManagedStackCheckResult:
        """
        Reconciles the managed stack with the external resource.
        """
        raise NotImplementedError()
