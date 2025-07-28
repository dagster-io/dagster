from typing import Optional, TypedDict, Union


class InputSelectOption(TypedDict):
    label: str
    value: str


class InputSelectField(TypedDict):
    select: str
    key: str
    options: list[InputSelectOption]
    hint: Optional[str]
    default: Optional[str]
    required: Optional[bool]
    multiple: Optional[bool]


class InputTextField(TypedDict):
    text: str
    key: str
    hint: Optional[str]
    default: Optional[str]
    required: Optional[bool]


BlockStepConfiguration = TypedDict(
    "BlockStepConfiguration",
    {
        "block": str,
        "key": Optional[str],
        "prompt": Optional[str],
        "fields": list[Union[InputSelectField, InputTextField]],
        "depends_on": Optional[list[str]],
        "if": Optional[str],
        "skip": Optional[str],
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

    def skip_if(self, skip_reason: Optional[str] = None):
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
