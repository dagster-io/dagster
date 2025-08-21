import functools
import sys
import textwrap
import traceback
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING, Annotated, Any, Callable, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict

from dagster import _check as check
from dagster._annotations import public
from dagster.components.resolved.errors import ResolutionException

try:
    # this type only exists in python 3.10+
    from types import UnionType  # type: ignore
except ImportError:
    UnionType = Union

if TYPE_CHECKING:
    from dagster.components.resolved.context import ResolutionContext


@public
@public
class Model(BaseModel):
    """pydantic BaseModel configured with recommended default settings for use with the Resolved framework.

    Extra fields are disallowed when instantiating this model to help catch errors earlier.

    Example:

    .. code-block:: python

        import dagster as dg

        class MyModel(dg.Resolvable, dg.Model):
            name: str
            age: int

        # raises exception
        MyModel(name="John", age=30, other="field")

    """

    model_config = ConfigDict(extra="forbid")


@dataclass
class ParentFn:
    callable: Callable[["ResolutionContext", Any], Any]


@dataclass
class AttrWithContextFn:
    callable: Callable[["ResolutionContext", Any], Any]


_default_fn = AttrWithContextFn(lambda context, field_value: context.resolve_value(field_value))

_passthrough_fn = AttrWithContextFn(lambda context, val: val)


def resolve_union(resolvers: Sequence["Resolver"], context: "ResolutionContext", field_value: Any):
    """Resolve a union typed field by trying each resolver in order until one succeeds.
    This attempts to mirror the behavior of the Union type in Pydantic using the left-to-right
    strategy. If all resolvers fail, a ResolutionException is raised.
    """
    accumulated_errors = []
    custom_resolvers = [r for r in resolvers if not r.is_default]
    default_resolvers = [r for r in resolvers if r.is_default]
    # the default resolver will pass through any value, so run those last
    for r in chain(custom_resolvers, default_resolvers):
        try:
            result = r.fn.callable(context, field_value)
            if result is not None:
                return result
        except Exception:
            accumulated_errors.append(traceback.format_exc())

    raise ResolutionException(
        "No resolver matched the field value"
        + "\n"
        + textwrap.indent(
            "\n".join(accumulated_errors),
            prefix="  ",
        ),
    )


@public
class Resolver:
    """Contains information on how to resolve a value from YAML into the corresponding :py:class:`Resolved` class field.

    You can attach a resolver to a field's type annotation to control how the value is resolved.

    Example:

    .. code-block:: python

        import datetime
        from typing import Annotated
        import dagster as dg

        def resolve_timestamp(
            context: dg.ResolutionContext,
            raw_timestamp: str,
        ) -> datetime.datetime:
            return datetime.datetime.fromisoformat(
                context.resolve_value(raw_timestamp, as_type=str),
            )

        class MyClass(dg.Resolvable, dg.Model):
            event: str
            # the yaml field will be a string, which is then parsed into a datetime object
            timestamp: Annotated[
                datetime.datetime,
                dg.Resolver(resolve_timestamp, model_field_type=str),
            ]
    """

    def __init__(
        self,
        fn: Union[ParentFn, AttrWithContextFn, Callable[["ResolutionContext", Any], Any]],
        *,
        model_field_name: Optional[str] = None,
        model_field_type: Optional[type] = None,
        description: Optional[str] = None,
        examples: Optional[list[Any]] = None,
        inject_before_resolve: bool = True,
    ):
        """Resolve this field by invoking the function which will receive the corresponding field value
        from the model.

        Args:
            fn (Callable[[ResolutionContext, Any], Any]): The custom resolution function.
            model_field_name (Optional[str]): Override the name of the field on the
                generated pydantic model. This is the name that to be used in yaml.
            model_field_type (Optional[type]): Override the type of this field on the
                generated pydantic model. This will define the schema used in yaml.
            description (Optional[str]): Description to add to the generated pydantic model.
                This will show up in documentation and IDEs during yaml editing.
            examples (Optional[list[Any]]): Example values that are valid when
                loading from yaml.
            inject_before_resolve (bool): If True (Default) string values will be evaluated
                to perform possible template resolution before calling the resolver function.
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
        self.description = description
        self.examples = examples
        self.inject_before_resolve = inject_before_resolve

        super().__init__()

    @staticmethod
    def from_model(fn: Callable[["ResolutionContext", Any], Any], **kwargs):
        """Resolve this field by invoking the function which will receive the entire parent model."""
        return Resolver(ParentFn(fn), **kwargs)

    @staticmethod
    def union(arg_resolver_pairs: Sequence[tuple[type, "Resolver"]]):
        field_types = tuple(r.model_field_type or t for t, r in arg_resolver_pairs)
        return Resolver(
            fn=functools.partial(resolve_union, [r for _, r in arg_resolver_pairs]),
            model_field_type=Union[field_types],  # type: ignore
        )

    @staticmethod
    def default(
        *,
        model_field_name: Optional[str] = None,
        model_field_type: Optional[type] = None,
        description: Optional[str] = None,
        examples: Optional[list[Any]] = None,
    ):
        """Default recursive resolution."""
        return Resolver(
            _default_fn,
            model_field_name=model_field_name,
            model_field_type=model_field_type,
            description=description,
            examples=examples,
            inject_before_resolve=False,
        )

    @staticmethod
    def passthrough(
        description: Optional[str] = None,
        examples: Optional[list[Any]] = None,
    ):
        """Resolve this field by returning the underlying value, without resolving any
        nested resolvers or processing any template variables.
        """
        return Resolver(
            _passthrough_fn,
            inject_before_resolve=False,
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

                # handle template injection
                if self.inject_before_resolve and isinstance(attr, str):
                    attr = context.resolve_value(attr)
                    if not isinstance(attr, str):
                        return attr

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
        return self.fn is _default_fn

    @property
    def resolves_from_parent_object(self) -> bool:
        return isinstance(self.fn, ParentFn)

    def with_outer_resolver(self, outer: "Resolver"):
        description = outer.description or self.description
        examples = outer.examples or self.examples
        return Resolver(
            self.fn,
            model_field_name=self.model_field_name,
            model_field_type=self.model_field_type,
            description=description,
            examples=examples,
            inject_before_resolve=self.inject_before_resolve,
        )


T = TypeVar("T")

Injected = Annotated[T, Resolver.default(model_field_type=str)]
