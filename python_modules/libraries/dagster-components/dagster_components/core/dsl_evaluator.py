from contextlib import contextmanager
from typing import Any, Generator, Mapping, Optional

from jinja2 import Template


class DslEvaluator:
    def __init__(self, dsl_context: Mapping[str, Any]):
        self.dsl_context = dsl_context

    @contextmanager
    def with_dsl_context(
        self, **dsl_context: Mapping[str, Any]
    ) -> Generator["DslEvaluator", None, None]:
        yield DslEvaluator({**self.dsl_context, **dsl_context})

    def eval(self, template: str, dsl_context: Optional[Mapping[str, Any]] = None) -> str:
        return Template(template).render({**self.dsl_context, **(dsl_context or {})})

    def eval_with_kwargs(self, template: str, **dsl_context: Mapping[str, Any]) -> str:
        return self.eval(template, dsl_context)
