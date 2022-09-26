import enum
import itertools
from abc import abstractmethod
from typing import List, NamedTuple, Optional, OrderedDict, Tuple, Union

import click

from dagster._core.definitions.assets_lazy import LazyAssetsDefinition


class ManagedStackError(enum.Enum):
    CANNOT_CONNECT = "cannot_connect"


class ManagedStackDiffSort(enum.Enum):
    BY_TYPE = "by_type"
    BY_KEY = "by_key"


class ManagedStackDiff(
    NamedTuple(
        "_ManagedStackDiff",
        [
            ("additions", List[str]),
            ("deletions", List[str]),
            ("modifications", List[str]),
            ("nested", OrderedDict[str, "ManagedStackDiff"]),
            ("sort", ManagedStackDiffSort),
        ],
    )
):
    def __new__(
        cls,
        additions: Optional[List[str]] = None,
        deletions: Optional[List[str]] = None,
        modifications: Optional[List[str]] = None,
        sort: Optional[ManagedStackDiffSort] = ManagedStackDiffSort.BY_TYPE,
    ):
        return super().__new__(
            cls, additions or [], deletions or [], modifications or [], OrderedDict({}), sort
        )

    def add(self, name: str, value: str) -> "ManagedStackDiff":
        return self._replace(additions=self.additions + [f"{name}: {value}"])

    def delete(self, name: str, value: str) -> "ManagedStackDiff":
        return self._replace(deletions=self.deletions + [f"{name}: {value}"])

    def modify(self, name: str, old_value: str, new_value: str) -> "ManagedStackDiff":
        return self._replace(
            modifications=self.modifications + [f"{name}: {old_value} -> {new_value}"]
        )

    def with_nested(self, name: str, nested: "ManagedStackDiff") -> "ManagedStackDiff":
        return self._replace(nested=OrderedDict(list(self.nested.items()) + [(name, nested)]))

    def join(self, other: "ManagedStackDiff") -> "ManagedStackDiff":
        return self._replace(
            additions=self.additions + other.additions,
            deletions=self.deletions + other.deletions,
            modifications=self.modifications + other.modifications,
            nested=OrderedDict(list(self.nested.items()) + list(other.nested.items())),
        )

    def __str__(self):
        additions_str = "\n".join(self.display_additions())
        deletions_str = "\n".join(self.display_deletions())
        modifications_str = "\n".join(self.display_modifications())
        return f"{additions_str}\n{deletions_str}\n{modifications_str}"

    def display_additions(self, indent: int = 0):
        my_additions = [
            click.style(f"{' ' * indent}+ {addition}", fg="green") for addition in self.additions
        ]

        if self.sort == ManagedStackDiffSort.BY_TYPE:
            nested_additions = {
                key: nested.display_additions(indent + 2) for key, nested in self.nested.items()
            }
            nested_additions = list(
                itertools.chain.from_iterable(
                    [
                        [f"{' ' * indent}+ {key}:"] + addition
                        for key, addition in nested_additions.items()
                        if addition
                    ]
                )
            )
            return my_additions + nested_additions
        else:
            return my_additions

    def display_deletions(self, indent: int = 0):
        my_deletions = [
            click.style(f"{' ' * indent}- {deletion}", fg="red") for deletion in self.deletions
        ]

        if self.sort == ManagedStackDiffSort.BY_TYPE:
            nested_deletions = {
                key: nested.display_deletions(indent + 2) for key, nested in self.nested.items()
            }
            nested_deletions = list(
                itertools.chain.from_iterable(
                    [
                        [f"{' ' * indent}- {key}:"] + deletion
                        for key, deletion in nested_deletions.items()
                        if deletion
                    ]
                )
            )
            return my_deletions + nested_deletions
        else:
            return my_deletions

    def style(self, changes: Tuple[List, List, List], text: str) -> str:
        if len(changes[1]) == 0 and len(changes[2]) == 0:
            return click.style(f"+ {text}:", fg="green")
        elif len(changes[0]) == 0 and len(changes[2]) == 0:
            return click.style(f"- {text}:", fg="red")
        return click.style(f"~ {text}:", fg="yellow")

    def display_modifications(self, indent: int = 0):
        my_modifications = [
            click.style(f"{' ' * indent}~ {modification}", fg="yellow")
            for modification in self.modifications
        ]

        if self.sort == ManagedStackDiffSort.BY_TYPE:
            nested_modifications = {
                key: nested.display_modifications(indent + 2) for key, nested in self.nested.items()
            }
            nested_modifications = list(
                itertools.chain.from_iterable(
                    [
                        [f"{' ' * indent}~ {key}:"] + modification
                        for key, modification in nested_modifications.items()
                        if modification
                    ]
                )
            )
            return my_modifications + nested_modifications
        else:
            nested_modifications = {
                key: (
                    nested.display_additions(indent + 2),
                    nested.display_deletions(indent + 2),
                    nested.display_modifications(indent + 2),
                )
                for key, nested in self.nested.items()
            }
            nested_modifications = list(
                itertools.chain.from_iterable(
                    [
                        [f"{' ' * indent}{self.style(modification, key)}"]
                        + modification[0]
                        + modification[1]
                        + modification[2]
                        for key, modification in nested_modifications.items()
                        if modification[0] or modification[1] or modification[2]
                    ]
                )
            )
            return my_modifications + nested_modifications

    # additions = self.additions
    #     if nested.additions:
    #         additions += [f" + {name}:"] + [f"  {line}" for line in nested.additions]
    #     deletions = self.deletions
    #     if nested.deletions:
    #         deletions += [f" - {name}:"] + [f"  {line}" for line in nested.deletions]
    #     modifications = self.modifications
    #     if nested.modifications:
    #         modifications += [f" ~ {name}:"] + [f"  {line}" for line in nested.modifications]
    #     return self._replace(additions=additions, deletions=deletions, modifications=modifications)


ManagedStackCheckResult = Union[ManagedStackDiff, ManagedStackError]


class ManagedStackAssetsDefinition(LazyAssetsDefinition):
    def __init__(self, unique_id: str):
        super().__init__(unique_id)

    @abstractmethod
    def check(self) -> ManagedStackCheckResult:
        """
        Returns whether the user provided config for the managed stack is in sync with the external resource.
        """
        raise NotImplementedError()

    @abstractmethod
    def apply(self):
        """
        Reconciles the managed stack with the external resource.
        """
        raise NotImplementedError()
