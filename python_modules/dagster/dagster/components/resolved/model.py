import sys
import traceback
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Any, Callable, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict

from dagster import _check as check

try:
    # this type only exists in python 3.10+
    from types import UnionType  # type: ignore
except ImportError:
    UnionType = Union

if TYPE_CHECKING:
    from dagster.components.resolved.context import ResolutionContext


class Model(BaseModel):
    """pydantic BaseModel configured to disallow extra fields in order to help catch errors earlier."""

    model_config = ConfigDict(extra="forbid")


def _recurse(context: "ResolutionContext", field_value):
    return context.resolve_value(field_value)


@dataclass
class ParentFn:
    callable: Callable[["ResolutionContext", Any], Any]


@dataclass
class AttrWithContextFn:
    callable: Callable[["ResolutionContext", Any], Any]


class Resolver:
    """Contains information on how to resolve a field from a model."""

    def __init__(
        self,
        fn: Union[ParentFn, AttrWithContextFn, Callable[["ResolutionContext", Any], Any]],
        model_field_name: Optional[str] = None,
        model_field_type: Optional[type] = None,
        can_inject: bool = False,
    ):
        """Resolve this field by invoking the function which will receive the corresponding field value
        from the model.
        """
        if not isinstance(fn, (ParentFn, AttrWithContextFn)):
            if not callable(fn):
                check.param_invariant(
                    callable(fn),
                    "fn",
                    f"must be callable if not ParentFn or AttrWithContextFn. Got {fn}",
                )
            self.fn = AttrWithContextFn(fn)
        else:
            self.fn = fn

        self.model_field_name = model_field_name
        self.model_field_type = model_field_type
        self.can_inject = can_inject

        super().__init__()

    @staticmethod
    def from_model(fn: Callable[["ResolutionContext", Any], Any], **kwargs):
        """Resolve this field by invoking the function which will receive the entire parent model."""
        return Resolver(ParentFn(fn), **kwargs)

    @staticmethod
    def default(**kwargs):
        """Default recursive resolution."""
        return Resolver(_recurse, **kwargs)

    def execute(
        self,
        context: "ResolutionContext",
        model: BaseModel,
        field_name: str,
    ) -> Any:
        from dagster.components.resolved.context import ResolutionException

        try:
            if isinstance(self.fn, ParentFn):
                return self.fn.callable(context, model)
            elif isinstance(self.fn, AttrWithContextFn):
                field_name = self.model_field_name or field_name
                attr = getattr(model, field_name)
                context = context.at_path(field_name)
                return self.fn.callable(context, attr)
        except ResolutionException:
            raise  # already processed
        except Exception:
            raise context.build_resolve_fn_exc(
                traceback.format_exception(*sys.exc_info()),
                field_name=field_name,
                model=model,
            ) from None

        raise ValueError(f"Unsupported Resolver type: {self.fn}")


T = TypeVar("T")

Injectable = Annotated[T, Resolver.default(can_inject=True)]
Injected = Annotated[T, Resolver.default(model_field_type=str)]
