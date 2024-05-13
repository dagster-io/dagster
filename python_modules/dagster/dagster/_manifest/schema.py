from typing import Protocol


class ExecutableManifest(Protocol):
    @property
    def kind(self) -> str: ...
