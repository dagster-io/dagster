from collections.abc import Sequence
from typing import Self

from typing_extensions import NotRequired, Required, TypedDict


class InputSelectOption(TypedDict):
    label: str
    value: str


class InputSelectField(TypedDict):
    select: str
    key: str
    options: list[InputSelectOption]
    hint: NotRequired[str | None]
    default: NotRequired[str | None]
    required: NotRequired[bool | None]
    multiple: NotRequired[bool | None]


class InputTextField(TypedDict):
    text: str
    key: str
    hint: NotRequired[str | None]
    default: NotRequired[str | None]
    required: NotRequired[bool | None]


class BlockStepConfiguration(TypedDict, closed=True, total=False):
    label: Required[str]
    block: str
    key: str | None
    prompt: str | None
    fields: list[InputSelectField | InputTextField]
    depends_on: list[str] | None
    skip: str | None
    # Covers the "if" key, which is a Python reserved word and cannot be used as
    # a class attribute. Buildkite uses "if" for conditional step execution.
    __extra_items__: str | None


class BlockStepBuilder:
    _step: BlockStepConfiguration

    def __init__(self, block: str, key: str | None = None) -> None:
        self._step: BlockStepConfiguration = {"label": block, "block": block}

        if key is not None:
            self._step["key"] = key

    def with_prompt(
        self,
        prompt: str,
        fields: list[InputSelectField | InputTextField] | None = None,
    ) -> Self:
        self._step["prompt"] = prompt
        if fields:
            self._step["fields"] = fields
        return self

    def skip_if(self, skip_reason: str | None = None) -> Self:
        if skip_reason:
            self._step["skip"] = skip_reason
        return self

    def with_condition(self, condition: str) -> Self:
        self._step["if"] = condition  # pyright: ignore[reportGeneralTypeIssues]
        return self

    def depends_on(self, dependencies: str | Sequence[str]) -> Self:
        self._step["depends_on"] = (
            [dependencies] if isinstance(dependencies, str) else list(dependencies)
        )
        return self

    def build(self) -> BlockStepConfiguration:
        return self._step
