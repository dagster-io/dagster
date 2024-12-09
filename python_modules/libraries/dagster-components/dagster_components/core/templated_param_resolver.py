from contextlib import contextmanager
from typing import Any, Generator, Mapping, Optional

from jinja2 import Template


class TemplatedParamResolver:
    def __init__(self, context_vars: Mapping[str, Any]):
        self.context_vars = context_vars

    @contextmanager
    def with_context_vars(
        self, **context_vars: Mapping[str, Any]
    ) -> Generator["TemplatedParamResolver", None, None]:
        yield TemplatedParamResolver({**self.context_vars, **context_vars})

    def resolve(self, template: str, context_vars: Optional[Mapping[str, Any]] = None) -> str:
        return Template(template).render({**self.context_vars, **(context_vars or {})})

    def resolve_with_kwargs(self, template: str, **dsl_context: Mapping[str, Any]) -> str:
        return self.resolve(template, dsl_context)
