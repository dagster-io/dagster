from typing import TypeVar

from dagster_shared.utils.warnings import (
    BetaWarning as BetaWarning,
    ConfigArgumentWarning as ConfigArgumentWarning,
    PreviewWarning as PreviewWarning,
    SupersessionWarning as SupersessionWarning,
    beta_warning as beta_warning,
    config_argument_warning as config_argument_warning,
    deprecation_warning as deprecation_warning,
    disable_dagster_warnings as disable_dagster_warnings,
    normalize_renamed_param as normalize_renamed_param,
    preview_warning as preview_warning,
    supersession_warning as supersession_warning,
)

from dagster._core.decorator_utils import Decoratable, apply_context_manager_decorator

T_Decoratable = TypeVar("T_Decoratable", bound=Decoratable)


# only lives here because dagster._core.decorator_utils has not been moved to dagster_shared
def suppress_dagster_warnings(__obj: T_Decoratable) -> T_Decoratable:
    """Mark a method/function as ignoring Dagster-generated warnings.
    This suppresses any `PreviewWarnings`, `BetaWarnings`, `SupersessionWarnings`
    or `DeprecationWarnings` when the function is called.

    Usage:

        .. code-block:: python

            @suppress_dagster_warnings
            def invokes_some_deprecated_stuff(my_arg):
                my_deprecated_function(my_arg)
    """
    return apply_context_manager_decorator(__obj, disable_dagster_warnings)
