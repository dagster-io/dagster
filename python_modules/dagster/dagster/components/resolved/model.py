import sys
import traceback
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Any, Callable, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict

from dagster import _check as check
from dagster._annotations import preview, public

try:
    # this type only exists in python 3.10+
    from types import UnionType  # type: ignore
except ImportError:
    UnionType = Union

if TYPE_CHECKING:
    from dagster.components.resolved.context import ResolutionContext


@public
@preview(emit_runtime_warning=False)
class Model(BaseModel):
    """pydantic BaseModel configured to disallow extra fields in order to help catch errors earlier."""

    model_config = ConfigDict(extra="forbid")


@dataclass
class ParentFn:
    callable: Callable[["ResolutionContext", Any], Any]


@dataclass
class AttrWithContextFn:
    callable: Callable[["ResolutionContext", Any], Any]


default_resolver = AttrWithContextFn(
    lambda context, field_value: context.resolve_value(field_value)
)


@public
@preview(emit_runtime_warning=False)
class Resolver:
    """Contains information on how to resolve a field from a model."""

    def __init__(
        self,
        fn: Union[ParentFn, AttrWithContextFn, Callable[["ResolutionContext", Any], Any]],
        *,
        model_field_name: Optional[str] = None,
        model_field_type: Optional[type] = None,
        can_inject: bool = False,
        description: Optional[str] = None,
        examples: Optional[list[Any]] = None,
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
        self.description = description
        self.examples = examples

        super().__init__()

    @staticmethod
    def from_model(fn: Callable[["ResolutionContext", Any], Any], **kwargs):
        """Resolve this field by invoking the function which will receive the entire parent model."""
        return Resolver(ParentFn(fn), **kwargs)

    @staticmethod
    def default(
        *,
        model_field_name: Optional[str] = None,
        model_field_type: Optional[type] = None,
        can_inject: bool = False,
        description: Optional[str] = None,
        examples: Optional[list[Any]] = None,
    ):
        """Default recursive resolution."""
        return Resolver(
            default_resolver,
            model_field_name=model_field_name,
            model_field_type=model_field_type,
            can_inject=can_inject,
            description=description,
            examples=examples,
        )

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

    @property
    def is_default(self):
        return self.fn is default_resolver

    @property
    def resolves_from_parent_object(self) -> bool:
        return isinstance(self.fn, ParentFn)

    def with_outer_resolver(self, outer: "Resolver"):
        description = outer.description or self.description
        examples = outer.examples or self.examples
        can_inject = outer.can_inject or self.can_inject
        return Resolver(
            self.fn,
            model_field_name=self.model_field_name,
            model_field_type=self.model_field_type,
            can_inject=can_inject,
            description=description,
            examples=examples,
        )


T = TypeVar("T")

Injectable = Annotated[T, Resolver.default(can_inject=True)]
Injected = Annotated[T, Resolver.default(model_field_type=str)]
