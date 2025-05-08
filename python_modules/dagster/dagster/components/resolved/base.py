import inspect
from collections.abc import Mapping, Sequence
from dataclasses import MISSING, fields, is_dataclass
from enum import Enum, auto
from functools import partial
from types import GenericAlias
from typing import Annotated, Any, Final, Literal, Optional, TypeVar, Union, get_args, get_origin

import yaml
from dagster_shared.record import get_record_annotations, get_record_defaults, is_record, record
from dagster_shared.yaml_utils import try_parse_yaml_with_source_position
from pydantic import BaseModel, PydanticSchemaGenerationError, create_model
from pydantic.fields import Field, FieldInfo
from typing_extensions import TypeGuard

from dagster import _check as check
from dagster._annotations import preview, public
from dagster._utils.pydantic_yaml import _parse_and_populate_model_with_annotated_errors
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.errors import ResolutionException
from dagster.components.resolved.model import Model, Resolver

try:
    # this type only exists in python 3.10+
    from types import UnionType  # type: ignore
except ImportError:
    UnionType = Union


class _TypeContainer(Enum):
    SEQUENCE = auto()
    OPTIONAL = auto()


_DERIVED_MODEL_REGISTRY = {}


@public
@preview(emit_runtime_warning=False)
class Resolvable:
    """This base class makes something able to "resolve" from yaml.

    This is done by:
    1) Deriving a pydantic model to provide as schema for the yaml.
    2) Resolving an instance of the class by recursing over an instance
    of the derived model loaded from schema compliant yaml and
    evaluating any template strings.

    The fields/__init__ arguments of the class can be Annotated with
    Resolver to customize the resolution or model derivation.
    """

    @classmethod
    def model(cls) -> type[BaseModel]:
        return derive_model_type(cls)

    @classmethod
    def resolve_from_model(cls, context: "ResolutionContext", model: BaseModel):
        return cls(**resolve_fields(model, cls, context))

    @classmethod
    def resolve_from_yaml(cls, yaml: str):
        parsed_and_src_tree = try_parse_yaml_with_source_position(yaml)
        model_cls = cls.model()
        if parsed_and_src_tree:
            model = _parse_and_populate_model_with_annotated_errors(
                cls=model_cls,
                obj_parse_root=parsed_and_src_tree,
                obj_key_path_prefix=[],
            )
        else:  # yaml parsed as None
            model = model_cls()
        # support adding scopes
        context = ResolutionContext.default(
            parsed_and_src_tree.source_position_tree if parsed_and_src_tree else None
        )
        return cls.resolve_from_model(context, model)

    @classmethod
    def resolve_from_dict(cls, dictionary: dict[str, Any]):
        # Convert dictionary to YAML string
        # default_flow_style=False makes it use block style instead of inline
        yaml_string = yaml.dump(
            dictionary,
            default_flow_style=False,
            sort_keys=False,  # Preserve dictionary order
            indent=2,  # Set indentation level
        )
        return cls.resolve_from_yaml(yaml_string)


# marker type for skipping kwargs and triggering defaults
# must be a string to make sure it is json serializable
_Unset: Final[str] = "__DAGSTER_UNSET_DEFAULT__"


def derive_model_type(
    target_type: type[Resolvable],
) -> type[BaseModel]:
    if target_type not in _DERIVED_MODEL_REGISTRY:
        model_name = f"{target_type.__name__}Model"

        model_fields: dict[
            str, Any
        ] = {}  # use Any to appease type checker when **-ing in to create_model

        for name, annotation_info in _get_annotations(target_type).items():
            field_resolver = _get_resolver(annotation_info.type, name)
            field_name = field_resolver.model_field_name or name
            field_type = field_resolver.model_field_type or annotation_info.type

            field_infos = []
            if annotation_info.field_info:
                field_infos.append(annotation_info.field_info)

            if annotation_info.has_default:
                # if the annotation has a serializable default
                # value, propagate it to the inner schema, otherwise
                # use a marker value that will cause the kwarg
                # to get omitted when we resolve fields in order
                # to trigger the default on the target type
                default_value = (
                    annotation_info.default
                    if type(annotation_info.default) in {int, float, str, bool, type(None)}
                    else _Unset
                )
                field_infos.append(
                    Field(
                        default=default_value,
                        description=field_resolver.description,
                        examples=field_resolver.examples,
                    ),
                )
            elif field_resolver.description or field_resolver.examples:
                field_infos.append(
                    Field(
                        description=field_resolver.description,
                        examples=field_resolver.examples,
                    )
                )

            if field_resolver.can_inject:  # derive and serve via model_field_type
                field_type = Union[field_type, str]

            model_fields[field_name] = (
                field_type,
                FieldInfo.merge_field_infos(*field_infos),
            )

        try:
            _DERIVED_MODEL_REGISTRY[target_type] = create_model(
                model_name,
                __base__=Model,
                **model_fields,
            )
        except PydanticSchemaGenerationError as e:
            raise ResolutionException(f"Unable to derive Model for {target_type}") from e

    return _DERIVED_MODEL_REGISTRY[target_type]


def _is_implicitly_resolved_type(annotation):
    if annotation in (int, float, str, bool, Any, type(None)):
        return True

    if _safe_is_subclass(annotation, Resolvable):
        return False

    if _safe_is_subclass(annotation, BaseModel):
        return True

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin in (Union, UnionType, list, Sequence, tuple, dict, Mapping) and all(
        _is_implicitly_resolved_type(arg) for arg in args
    ):
        return True

    if origin is Literal and all(_is_implicitly_resolved_type(type(arg)) for arg in args):
        return True

    return False


@record
class AnnotationInfo:
    type: Any
    default: Any
    has_default: bool
    field_info: Optional[FieldInfo]


def _get_annotations(
    resolved_type: type[Resolvable],
) -> dict[str, AnnotationInfo]:
    annotations: dict[str, AnnotationInfo] = {}
    init_kwargs = _get_init_kwargs(resolved_type)
    if is_dataclass(resolved_type):
        for f in fields(resolved_type):
            has_default = f.default is not MISSING or f.default_factory is not MISSING
            annotations[f.name] = AnnotationInfo(
                type=f.type,
                default=f.default,
                has_default=has_default,
                field_info=None,
            )
        return annotations
    elif _safe_is_subclass(resolved_type, BaseModel):
        for name, field_info in resolved_type.model_fields.items():
            has_default = not field_info.is_required()
            annotations[name] = AnnotationInfo(
                type=field_info.rebuild_annotation(),
                default=field_info.default,
                has_default=has_default,
                field_info=field_info,
            )
        return annotations
    elif is_record(resolved_type):
        defaults = get_record_defaults(resolved_type)
        for name, ttype in get_record_annotations(resolved_type).items():
            annotations[name] = AnnotationInfo(
                type=ttype,
                default=defaults[name] if name in defaults else None,
                has_default=name in defaults,
                field_info=None,
            )
        return annotations
    elif init_kwargs is not None:
        return init_kwargs
    else:
        raise ResolutionException(
            f"Invalid Resolvable type {resolved_type} could not determine fields, expected:\n"
            "* class with __init__\n"
            "* @dataclass\n"
            "* pydantic Model\n"
            "* @record\n"
        )


def _get_init_kwargs(
    target_type: type[Resolvable],
) -> Optional[dict[str, AnnotationInfo]]:
    if target_type.__init__ is object.__init__:
        return None

    sig = inspect.signature(target_type.__init__)
    fields: dict[str, AnnotationInfo] = {}

    skipped_self = False
    for name, param in sig.parameters.items():
        if not skipped_self:
            skipped_self = True
            continue

        if param.kind == param.POSITIONAL_ONLY:
            raise ResolutionException(
                f"Invalid Resolvable type {target_type}: __init__ contains positional only parameter."
            )
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        if param.annotation == param.empty:
            raise ResolutionException(
                f"Invalid Resolvable type {target_type}: __init__ parameter {name} has no type hint."
            )

        fields[name] = AnnotationInfo(
            type=param.annotation,
            default=param.default,
            has_default=param.default is not param.empty,
            field_info=None,
        )
    return fields


def resolve_fields(
    model: BaseModel,
    resolved_cls: type[Resolvable],
    context: "ResolutionContext",
) -> Mapping[str, Any]:
    """Returns a mapping of field names to resolved values for those fields."""
    field_resolvers = {
        field_name: _get_resolver(annotation_info.type, field_name)
        for field_name, annotation_info in _get_annotations(resolved_cls).items()
    }

    return {
        field_name: resolver.execute(context=context, model=model, field_name=field_name)
        for field_name, resolver in field_resolvers.items()
        # filter out unset fields to trigger defaults
        if (resolver.model_field_name or field_name) in model.model_dump(exclude_unset=True)
        and getattr(model, resolver.model_field_name or field_name) != _Unset
    }


TType = TypeVar("TType", bound=type)


def _safe_is_subclass(obj, cls: TType) -> TypeGuard[type[TType]]:
    return (
        isinstance(obj, type)
        and not isinstance(obj, GenericAlias)  # prevent exceptions on 3.9
        and issubclass(obj, cls)
    )


def _get_resolver(annotation: Any, field_name: str) -> "Resolver":
    origin = get_origin(annotation)
    args = get_args(annotation)

    # explicit field level Resolver
    if origin is Annotated:
        resolver = next((arg for arg in args if isinstance(arg, Resolver)), None)
        if resolver:
            # if the outer resolver is default, see if there is a nested one
            if resolver.is_default:
                nested = _dig_for_resolver(args[0], [])
                if nested:
                    return nested.with_outer_resolver(resolver)

            check.invariant(
                _is_implicitly_resolved_type(args[0]) or resolver.model_field_type,
                f"Resolver for {field_name} must define model_field_type, {args[0]} is not model compliant.",
            )
            return resolver

    if _is_implicitly_resolved_type(annotation):
        return Resolver.default()

    # nested or implicit
    res = _dig_for_resolver(annotation, [])
    if res:
        return res
    raise ResolutionException(
        "Could not derive resolver for annotation\n"
        f"  {field_name}: {annotation}\n"
        "Field types are expected to be:\n"
        "* serializable types such as str, float, int, bool, list, etc\n"
        "* Resolvable subclasses\n"
        "* pydantic Models\n"
        "* Annotated with an appropriate Resolver"
    )


def _dig_for_resolver(annotation, path: Sequence[_TypeContainer]) -> Optional[Resolver]:
    origin = get_origin(annotation)
    args = get_args(annotation)
    if _safe_is_subclass(annotation, Resolvable):
        return Resolver(
            partial(
                _resolve_at_path,
                container_path=path,
                resolver=annotation.resolve_from_model,
            ),
            model_field_type=_wrap(annotation.model(), path),
        )

    if origin is Annotated:
        resolver = next((arg for arg in args if isinstance(arg, Resolver)), None)
        if resolver:
            check.invariant(
                _is_implicitly_resolved_type(args[0]) or resolver.model_field_type,
                f"Nested resolver must define model_field_type {args[0]} is not model compliant.",
            )
            # need to ensure nested resolvers set their model type
            if resolver.resolves_from_parent_object and path:
                raise ResolutionException(
                    f"Resolver.from_model found nested within {list(p.name for p in path)}. "
                    "Resolver.from_model can only be used on the outer most Annotated wrapper."
                )

            return Resolver(
                resolver.fn.__class__(
                    partial(
                        _resolve_at_path,
                        container_path=path,
                        resolver=resolver.fn.callable,
                    )
                ),
                model_field_type=_wrap(resolver.model_field_type or args[0], path),
            )
        annotated_type = args[0]
        if _is_implicitly_resolved_type(annotated_type):
            return Resolver.default()

        return _dig_for_resolver(annotated_type, path)

    if origin in (Union, UnionType) and len(args) == 2:
        left_t, right_t = args
        if right_t is type(None):
            res = _dig_for_resolver(left_t, [*path, _TypeContainer.OPTIONAL])
            if res:
                return res

    elif origin in (
        Sequence,
        tuple,
        list,
    ):  # should look for tuple[T, ...] specifically
        res = _dig_for_resolver(args[0], [*path, _TypeContainer.SEQUENCE])
        if res:
            return res


def _wrap(ttype, path: Sequence[_TypeContainer]):
    result_type = ttype
    for container in reversed(path):
        if container is _TypeContainer.OPTIONAL:
            result_type = Optional[result_type]
        elif container is _TypeContainer.SEQUENCE:
            # use tuple instead of Sequence for perf
            result_type = tuple[result_type, ...]
        else:
            check.assert_never(container)
    return result_type


def _resolve_at_path(
    context: "ResolutionContext",
    value: Any,
    container_path: Sequence[_TypeContainer],
    resolver,
):
    if not container_path:
        return resolver(context, value)

    container = container_path[0]
    inner_path = container_path[1:]
    if container is _TypeContainer.OPTIONAL:
        return _resolve_at_path(context, value, inner_path, resolver) if value is not None else None
    elif container is _TypeContainer.SEQUENCE:
        return [
            _resolve_at_path(context.at_path(idx), i, inner_path, resolver)
            for idx, i in enumerate(value)
        ]

    check.assert_never(container)
