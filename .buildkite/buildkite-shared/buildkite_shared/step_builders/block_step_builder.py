from typing import TypedDict


class InputSelectOption(TypedDict):
    label: str
    value: str


class InputSelectField(TypedDict):
    select: str
    key: str
    options: list[InputSelectOption]
    hint: str | None
    default: str | None
    required: bool | None
    multiple: bool | None


class InputTextField(TypedDict):
    text: str
    key: str
    hint: str | None
    default: str | None
    required: bool | None


BlockStepConfiguration = TypedDict(
    "BlockStepConfiguration",
    {
        "block": str,
        "key": str | None,
        "prompt": str | None,
        "fields": list[InputSelectField | InputTextField],
        "depends_on": list[str] | None,
        "if": str | None,
        "skip": str | None,
    },
    total=False,
)


class BlockStepBuilder:
    _step: BlockStepConfiguration

    def __init__(self, block, key=None):
        self._step = {"block": block}

        if key is not None:
            self._step["key"] = key

    def with_prompt(self, prompt, fields=None):
        self._step["prompt"] = prompt
        if fields:
            self._step["fields"] = fields
        return self

    def skip_if(self, skip_reason: str | None = None):
        if skip_reason:
            self._step["skip"] = skip_reason
        return self

    def with_condition(self, condition):
        self._step["if"] = condition
        return self

    def depends_on(self, dependencies):
        self._step["depends_on"] = dependencies
        return self

    def build(self):
        return self._step
