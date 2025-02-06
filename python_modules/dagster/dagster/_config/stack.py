from collections.abc import Iterator, Sequence
from typing import Optional

import dagster._check as check
from dagster._record import record


@record
class EvaluationStackEntry:
    parent: Optional["EvaluationStackEntry"]

    @property
    def entries(self) -> Sequence["EvaluationStackEntry"]:
        return list(self.iter_entries())

    def iter_entries(self) -> Iterator["EvaluationStackEntry"]:
        if self.parent:
            yield from self.parent.iter_entries()

        if self:
            yield self

    @property
    def levels(self) -> Sequence[str]:
        return [
            entry.field_name
            for entry in self.entries
            if isinstance(entry, EvaluationStackPathEntry)
        ]

    def for_field(self, field_name: str) -> "EvaluationStackEntry":
        return EvaluationStackPathEntry(
            field_name=field_name,
            parent=self,
        )

    def for_array_index(self, list_index: int) -> "EvaluationStackEntry":
        return EvaluationStackListItemEntry(
            list_index=list_index,
            parent=self,
        )

    def for_map_key(self, map_key: object) -> "EvaluationStackEntry":
        return EvaluationStackMapKeyEntry(
            map_key=map_key,
            parent=self,
        )

    def for_map_value(self, map_key: object) -> "EvaluationStackEntry":
        return EvaluationStackMapValueEntry(
            map_key=map_key,
            parent=self,
        )


@record
class EvaluationStackPathEntry(EvaluationStackEntry):
    field_name: str


@record
class EvaluationStackListItemEntry(EvaluationStackEntry):
    list_index: int


@record
class EvaluationStackMapKeyEntry(EvaluationStackEntry):
    map_key: object


@record
class EvaluationStackMapValueEntry(EvaluationStackEntry):
    map_key: object


@record
class EvaluationStackRoot(EvaluationStackEntry):
    parent: Optional["EvaluationStackEntry"] = None

    def iter_entries(self):
        yield from []


def get_friendly_path_msg(stack: EvaluationStackEntry) -> str:
    return get_friendly_path_info(stack)[0]


def get_friendly_path_info(stack: EvaluationStackEntry) -> tuple[str, str]:
    if isinstance(stack, EvaluationStackRoot):
        path = ""
        path_msg = "at the root"
    else:
        comps = ["root"]
        for entry in stack.entries:
            if isinstance(entry, EvaluationStackPathEntry):
                comp = ":" + entry.field_name
                comps.append(comp)
            elif isinstance(entry, EvaluationStackListItemEntry):
                comps.append(f"[{entry.list_index}]")
            elif isinstance(entry, EvaluationStackMapKeyEntry):
                comp = ":" + repr(entry.map_key) + ":key"
                comps.append(comp)
            elif isinstance(entry, EvaluationStackMapValueEntry):
                comp = ":" + repr(entry.map_key) + ":value"
                comps.append(comp)
            else:
                check.failed("unsupported")

        path = "".join(comps)
        path_msg = "at path " + path
    return path_msg, path
