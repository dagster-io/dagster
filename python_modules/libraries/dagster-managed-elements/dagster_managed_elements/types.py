import enum
from abc import ABC, abstractmethod
from typing import Any, NamedTuple, Optional, OrderedDict, Sequence, Tuple, Union

import click
import dagster._check as check


class ManagedElementError(enum.Enum):
    CANNOT_CONNECT = "cannot_connect"


SANITIZE_KEY_KEYWORDS = ["password", "token", "secret", "ssh_key", "credentials"]
SANITIZE_KEY_EXACT_MATCHES = ["pat"]

SECRET_MASK_VALUE = "**********"


def is_key_secret(key: str):
    """
    Rudamentary check to see if a config key is a secret value.
    """
    return any(keyword in key for keyword in SANITIZE_KEY_KEYWORDS) or any(
        match == key for match in SANITIZE_KEY_EXACT_MATCHES
    )


def _sanitize(key: str, value: str):
    """
    Rudamentary sanitization of values so we can avoid printing passwords
    to the console.
    """
    if is_key_secret(key):
        return SECRET_MASK_VALUE
    return value


class DiffData(NamedTuple("_DiffData", [("key", str), ("value", Any)])):
    def __new__(cls, key: str, value: str):
        return super(DiffData, cls).__new__(
            cls,
            key=check.str_param(key, "key"),
            value=value,
        )

    def __str__(self):
        return f"Key: {self.key}, Value: {self.value}"


class ModifiedDiffData(
    NamedTuple("_ModifiedDiffData", [("key", str), ("old_value", Any), ("new_value", Any)])
):
    def __new__(cls, key: str, old_value: Any, new_value: Any):
        return super(ModifiedDiffData, cls).__new__(
            cls, key=check.str_param(key, "key"), old_value=old_value, new_value=new_value
        )

    def __str__(self):
        return f"Key: {self.key}, Old Value: {self.old_value}, New Value: {self.new_value}"


class ManagedElementDiff(
    NamedTuple(
        "_ManagedElementDiff",
        [
            ("additions", Sequence[DiffData]),
            ("deletions", Sequence[DiffData]),
            ("modifications", Sequence[ModifiedDiffData]),
            ("nested", OrderedDict[str, "ManagedElementDiff"]),
        ],
    )
):
    """
    Utility class representing the diff between configured and deployed managed element. Can be rendered to a
    color-coded, user-friendly string.
    """

    def __new__(
        cls,
        additions: Optional[Sequence[DiffData]] = None,
        deletions: Optional[Sequence[DiffData]] = None,
        modifications: Optional[Sequence[ModifiedDiffData]] = None,
    ):
        additions = check.opt_sequence_param(additions, "additions", of_type=DiffData)
        deletions = check.opt_sequence_param(deletions, "deletions", of_type=DiffData)
        modifications = check.opt_sequence_param(
            modifications, "modifications", of_type=ModifiedDiffData
        )

        return super().__new__(
            cls,
            additions,
            deletions,
            modifications,
            OrderedDict({}),
        )

    def add(self, name: str, value: Any) -> "ManagedElementDiff":
        """
        Adds an addition entry to the diff.
        """
        check.str_param(name, "name")

        return self._replace(additions=[*self.additions, DiffData(name, value)])

    def delete(self, name: str, value: Any) -> "ManagedElementDiff":
        """
        Adds a deletion entry to the diff.
        """
        check.str_param(name, "name")

        return self._replace(deletions=[*self.deletions, DiffData(name, value)])

    def modify(self, name: str, old_value: Any, new_value: Any) -> "ManagedElementDiff":
        """
        Adds a modification entry to the diff.
        """
        check.str_param(name, "name")

        return self._replace(
            modifications=[*self.modifications, ModifiedDiffData(name, old_value, new_value)]
        )

    def with_nested(self, name: str, nested: "ManagedElementDiff") -> "ManagedElementDiff":
        """
        Adds the nested diff as a child of the current diff.
        """
        check.str_param(name, "name")
        check.inst_param(nested, "nested", ManagedElementDiff)

        return self._replace(nested=OrderedDict(list(self.nested.items()) + [(name, nested)]))

    def join(self, other: "ManagedElementDiff") -> "ManagedElementDiff":
        """
        Combines two diff objects into a single diff object.
        """
        check.inst_param(other, "other", ManagedElementDiff)

        return self._replace(
            additions=[*self.additions, *other.additions],
            deletions=[*self.deletions, *other.deletions],
            modifications=[*self.modifications, *other.modifications],
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

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ManagedElementDiff):
            return False

        return (
            sorted(self.additions, key=lambda x: x[0])
            == sorted(other.additions, key=lambda x: x[0])
            and sorted(self.deletions, key=lambda x: x[0])
            == sorted(other.deletions, key=lambda x: x[0])
            and sorted(self.modifications, key=lambda x: x[0])
            == sorted(other.modifications, key=lambda x: x[0])
            and sorted(list(self.nested.items()), key=lambda x: x[0])
            == sorted(list(other.nested.items()), key=lambda x: x[0])
        )

    def get_diff_display_entries(
        self, indent: int = 0
    ) -> Tuple[Sequence[str], Sequence[str], Sequence[str]]:
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
                    click.style(f"{' ' * indent}+ {key}:", fg="green"),
                    *nested_additions,
                ]
            elif len(nested_additions) == 0 and len(nested_modifications) == 0:
                # If there are only deletions, display the nested entry as a deletion
                my_deletions += [
                    click.style(f"{' ' * indent}- {key}:", fg="red"),
                    *nested_deletions,
                ]
            else:
                # Otherwise, display the nested entry as a modification
                my_modifications += [
                    click.style(f"{' ' * indent}~ {key}:", fg="yellow"),
                    *nested_additions,
                    *nested_deletions,
                    *nested_modifications,
                ]

        return (my_additions, my_deletions, my_modifications)


# Union type representing the status of a managed element - can either
# return the (potentially empty) diff between the configured and deployed
# stack, or an error.
ManagedElementCheckResult = Union[ManagedElementDiff, ManagedElementError]


class ManagedElementReconciler(ABC):
    """
    Base class which defines the interface for checking and reconciling a managed element.

    Typically, the constructor will take in a set of resources or user configuration. The
    implementations of the check and apply methods will then use this configuration to
    determine the diff between the configured and deployed stack, and to apply the
    configuration to the deployed stack.
    """

    @abstractmethod
    def check(self, **kwargs) -> ManagedElementCheckResult:
        """
        Returns whether the user provided config for the managed element is in sync with the external resource.

        kwargs contains any optional user-specified arguments to the check command.
        """
        raise NotImplementedError()

    @abstractmethod
    def apply(self, **kwargs) -> ManagedElementCheckResult:
        """
        Reconciles the managed element with the external resource, returning the applied diff.

        kwargs contains any optional user-specified arguments to the apply command.
        """
        raise NotImplementedError()
