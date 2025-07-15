import inspect
from typing import Any, Callable, Optional, Union, overload

from typing_extensions import TypeAlias

from dagster._annotations import public

TemplateVarFn: TypeAlias = Callable[..., Any]

TEMPLATE_VAR_ATTR = "__dagster_template_var"


@overload
def template_var(fn: TemplateVarFn) -> TemplateVarFn: ...


@overload
def template_var() -> Callable[[TemplateVarFn], TemplateVarFn]: ...


@public
def template_var(
    fn: Optional[TemplateVarFn] = None,
) -> Union[TemplateVarFn, Callable[[TemplateVarFn], TemplateVarFn]]:
    """A decorator that marks a functions as a template variables for use in Dagster component
    YAML files.

    Template variables allow you to inject dynamic values into component YAML configurations by
    calling Python functions during the component loading process. This enables parameterization
    of component definitions with computed values, environment variables, or other dynamic data.

    Template variables can return simple values or callable functions. When a template variable
    returns a function, it can be invoked in YAML with parameters using function call syntax
    within the template string (e.g., "{{ func_name('arg1', 'arg2') }}").

    The decorator can be used in two ways:
    1. As a bare decorator: @template_var
    2. As a decorator with parentheses: @template_var()

    Functions decorated with @template_var can accept 0 or 1 parameters:
    - 0 parameters: Simple value generation or function factory
    - 1 parameter: Receives ComponentDeclLoadContext for accessing component loading context. This is for cases when the udf needs access to information about the project, such as its location in the file system.

    Args:
        fn: The function to decorate as a template variable. If None, returns a decorator
            function that can be applied to the target function.

    Returns:
        Either the decorated function (if fn is provided) or a decorator function that
        can be applied to mark a function as a template variable.

    Examples:
        Basic usage with no parameters:

        .. code-block:: python

            @template_var
            def current_timestamp():
                return int(time.time())

        Usage with context parameter:

        .. code-block:: python

            @template_var
            def component_name(context: ComponentDeclLoadContext):
                return context.path.name

        Returning a function for parameterized template usage:

        .. code-block:: python

            @template_var
            def env_var():
                def get_env_var(name: str, default: str = ""):
                    return os.getenv(name, default)
                return get_env_var

            @template_var
            def path_join():
                def join_paths(*parts: str) -> str:
                    return os.path.join(*parts)
                return join_paths

        Usage in component YAML:

        .. code-block:: yaml

            # defs.yaml
            type: my_component.MyComponent
            attributes:
              name: "{{ component_name }}"
              timestamp: "{{ current_timestamp }}"
              database_url: "{{ env_var('DATABASE_URL', 'sqlite:///default.db') }}"
              config_path: "{{ path_join('/etc', 'myapp', 'config.yaml') }}"

    Note:
        Template variable functions are discovered automatically by the component loading
        system when specified in the `template_vars_module` field of a component YAML file.
        The functions are then available for use in YAML value templating using double
        curly brace syntax: {{ function_name }}.

        When a template variable returns a function, that function can be called with
        parameters directly in the YAML template string. This pattern is useful for
        creating reusable utilities like environment variable lookups, path operations,
        or string formatting functions that can be parameterized at the YAML level.
    """

    def decorator(func: TemplateVarFn) -> TemplateVarFn:
        setattr(func, TEMPLATE_VAR_ATTR, True)
        return func

    if fn is None:
        return decorator
    else:
        return decorator(fn)


def is_template_var(obj: Any) -> bool:
    return getattr(obj, TEMPLATE_VAR_ATTR, False)


def find_inline_template_vars_in_module(module: Any) -> dict[str, TemplateVarFn]:
    """Finds all template functions in the given module.

    Args:
        module: The module to search for template functions

    Returns:
        dict[str, TemplateVarFn]: A dictionary of template variable functions indexed by name
    """
    return {name: obj for name, obj in inspect.getmembers(module, is_template_var)}


def is_staticmethod(cls, method):
    """Check if a method is a static method by examining the class descriptor.

    Args:
        cls: The class where the method is defined
        method: The method reference (e.g., cls.method_name)

    Returns:
        bool: True if the method is a static method, False otherwise
    """
    # Get the method name from the method reference
    if not hasattr(method, "__name__"):
        return False

    method_name = method.__name__

    # Check the class hierarchy to find where this method is defined
    for base_cls in inspect.getmro(cls):
        if method_name in base_cls.__dict__:
            method_descriptor = base_cls.__dict__[method_name]
            return isinstance(method_descriptor, staticmethod)

    return False


def get_static_template_vars(cls: type) -> dict[str, TemplateVarFn]:
    """Find all staticmethods in a class that can be used as template variables.

    Args:
        cls: The class to search through

    Returns:
        A dictionary mapping method names to their callable functions for each matching staticmethod
    """
    results = {}
    for name, method in cls.__dict__.items():
        if is_staticmethod(cls, method):
            # Get the actual function from the staticmethod wrapper
            func = method.__get__(None, cls)
            if is_template_var(func):
                if len(inspect.signature(func).parameters) > 0:
                    raise ValueError(f"Static template var {name} must not take any arguments")
                results[name] = func()

    return results
