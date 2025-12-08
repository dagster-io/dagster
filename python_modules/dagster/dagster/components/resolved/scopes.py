"""Scope objects for use in component template resolution."""

import os
import warnings
from typing import Any, Optional, Union

from dagster.components.resolved.errors import ResolutionException


class EnvScope:
    """Provides access to environment variables within templates.

    Available via `{{ env.* }}` in component YAML files.
    """

    def __call__(self, key: str, default: Optional[Union[str, Any]] = ...) -> Optional[str]:
        value = os.environ.get(key, default=default)
        if value is ...:
            raise ResolutionException(
                f"Environment variable {key} is not set and no default value was provided."
                f" To provide a default value, use e.g. `env('{key}', 'default_value')`."
            )
        return value

    def __getattr__(self, key: str) -> Optional[str]:
        # jinja2 applies a hasattr check to any scope fn - we avoid raising our own exception
        # for this access
        if key.startswith("jinja"):
            raise AttributeError(f"{key} not found")

        return os.environ.get(key)

    def __getitem__(self, key: str) -> Optional[str]:
        raise ResolutionException(
            f"To access environment variables, use dot access or the `env` function, e.g. `env.{key}` or `env('{key}')`"
        )


class WrappedObjectScope:
    """Base class for wrapping an object and exposing its attributes in template scope.

    This allows us to expose Python objects (like modules or context objects) to Jinja templates
    with explicit attribute whitelisting.

    Args:
        wrapped_object: The object to wrap and expose to templates
        accessible_attributes: Set of attribute names that are allowed to be accessed from templates.
                              Only these attributes will be accessible via {{ scope.attr }}
    """

    def __init__(self, wrapped_object: Any, accessible_attributes: set[str]):
        self._wrapped_object = wrapped_object
        self._accessible_attributes = accessible_attributes

    def __getattr__(self, name: str):
        """Allow access to whitelisted wrapped object attributes."""
        # jinja2 applies a hasattr check to any scope fn - we avoid raising our own exception
        # for this access
        if name.startswith("jinja") or name.startswith("_"):
            raise AttributeError(f"{name} not found")
        # Check if this attribute is whitelisted
        if name not in self._accessible_attributes:
            raise AttributeError(
                f"Attribute '{name}' is not accessible. "
                f"Available attributes: {', '.join(sorted(self._accessible_attributes))}"
            )

        return getattr(self._wrapped_object, name)


class DgScope(WrappedObjectScope):
    """Provides access to Dagster definitions and utilities within templates.

    Available via `{{ dg.* }}` in component YAML files.

    Examples:
        {{ dg.AutomationCondition.eager() }}
        {{ dg.DailyPartitionsDefinition(start_date="2024-01-01") }}
    """

    def __init__(self):
        import dagster as dg

        accessible_attributes = {
            "AutomationCondition",
            "FreshnessPolicy",
            "DailyPartitionsDefinition",
            "WeeklyPartitionsDefinition",
            "MonthlyPartitionsDefinition",
            "HourlyPartitionsDefinition",
            "StaticPartitionsDefinition",
            "TimeWindowPartitionsDefinition",
        }

        super().__init__(dg, accessible_attributes)


class DatetimeScope(WrappedObjectScope):
    """Provides access to Python datetime utilities within templates.

    Available via `{{ datetime.* }}` in component YAML files.

    Examples:
        {{ datetime.datetime.now() }}
        {{ datetime.timedelta(days=7) }}
    """

    def __init__(self):
        import datetime

        accessible_attributes = {"datetime", "timedelta"}

        super().__init__(datetime, accessible_attributes)


class LoadContextScope(WrappedObjectScope):
    """Provides access to component loading utilities within templates.

    Available via `{{ context.* }}` in component YAML files.

    Examples:
        {{ context.project_root }}/data/input.csv
        {{ context.load_component("other_component") }}
        {{ context.build_defs("submodule") }}
    """

    def __init__(self, context):
        accessible_attributes = {
            "load_component",
            "build_defs",
            "project_root",
        }

        super().__init__(context, accessible_attributes)

    @property
    def project_root(self) -> str:
        # override here so we can resolve the project_root to a string
        return str(self._wrapped_object.project_root.resolve())


class DeprecatedScope:
    """Wrapper that provides backward compatibility for deprecated scope variables.

    Emits a deprecation warning whenever the variable is accessed.
    """

    def __init__(self, old_name: str, new_name: str, value: Any):
        self._old_name = old_name
        self._new_name = new_name
        self._value = value

    def _warn(self):
        warnings.warn(
            f"Accessing `{{{{{self._old_name}}}}}` is deprecated and will be "
            f"removed in Dagster 1.13.0. Use `{{{{{self._new_name}}}}}` instead.",
            DeprecationWarning,
            stacklevel=4,
        )

    def __call__(self, *args, **kwargs):
        self._warn()
        return self._value(*args, **kwargs)

    def __getattr__(self, key: str):
        # jinja2 applies a hasattr check to any scope fn - we avoid raising our own exception
        # for this access
        if key.startswith("jinja") or key.startswith("_"):
            raise AttributeError(f"{key} not found")

        self._warn()
        return getattr(self._value, key)

    def __getitem__(self, key: str):
        self._warn()
        return self._value[key]

    def __str__(self):
        self._warn()
        return str(self._value)
