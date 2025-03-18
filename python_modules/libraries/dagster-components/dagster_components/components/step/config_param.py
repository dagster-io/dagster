import inspect
from typing import Annotated, Any, Optional

from dagster._config.field import Field
from dagster._config.pythonic_config.conversion_utils import infer_schema_from_config_annotation
from typing_extensions import TypeVar

CONFIG_PARAM_METADATA = "config_param"

T = TypeVar("T")
ConfigParam = Annotated[T, CONFIG_PARAM_METADATA]


def has_config_param_annotation(annotation: Optional[type[Any]]) -> bool:
    return bool(
        annotation
        and hasattr(annotation, "__metadata__")
        and getattr(annotation, "__metadata__") == (CONFIG_PARAM_METADATA,)
    )


def config_schema_from_config_cls(config_cls: Optional[type]) -> Optional[Field]:
    return (
        infer_schema_from_config_annotation(
            model_cls=config_cls,
            config_arg_default=inspect.Parameter.empty,
        )
        if config_cls
        else None
    )
