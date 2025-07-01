import hashlib
import json
from collections import defaultdict
from collections.abc import Sequence

from dagster._core.errors import DagsterInvalidDefinitionError

# In the Dagster UI users can select partition ranges following the format '2022-01-13...2022-01-14'
# "..." is an invalid substring in partition keys
# The other escape characters are characters that may not display in the Dagster UI.
INVALID_PARTITION_SUBSTRINGS = ["...", "\a", "\b", "\f", "\n", "\r", "\t", "\v", "\0"]


def raise_error_on_invalid_partition_key_substring(partition_keys: Sequence[str]) -> None:
    for partition_key in partition_keys:
        found_invalid_substrs = [
            invalid_substr
            for invalid_substr in INVALID_PARTITION_SUBSTRINGS
            if invalid_substr in partition_key
        ]
        if found_invalid_substrs:
            raise DagsterInvalidDefinitionError(
                f"{found_invalid_substrs} are invalid substrings in a partition key"
            )


def raise_error_on_duplicate_partition_keys(partition_keys: Sequence[str]) -> None:
    counts: dict[str, int] = defaultdict(lambda: 0)
    for partition_key in partition_keys:
        counts[partition_key] += 1
    found_duplicates = [key for key in counts.keys() if counts[key] > 1]
    if found_duplicates:
        raise DagsterInvalidDefinitionError(
            "Partition keys must be unique. Duplicate instances of partition keys:"
            f" {found_duplicates}."
        )


def generate_partition_key_based_definition_id(partition_keys: Sequence[str]) -> str:
    return hashlib.sha1(json.dumps(partition_keys).encode("utf-8")).hexdigest()
