import inspect
from collections.abc import Generator
from typing import TYPE_CHECKING, Any, Callable, Optional, Union, overload

from typing_extensions import TypeAlias

from dagster._symbol_annotations.public import public

if TYPE_CHECKING:
    from dagster.components.core.context import ComponentDeclLoadContext

# Template variable functions must have 0 or 1 parameters.
# When 1 parameter is present, it must be ComponentLoadContext.
TemplateVarFn: TypeAlias = Callable[..., Any]
"""Type alias for template variable functions.

Template variable functions are constrained to two specific signatures:

**Valid Signatures:**
    - ``() -> Any`` - Zero parameters for static values computed at load time
    - ``(context: ComponentLoadContext) -> Any`` - Single context parameter for context-aware values

**Type Constraints:**
    - Must have exactly 0 or 1 parameters (no more, no less)
    - If 1 parameter is present, it must be typed as ``ComponentLoadContext``
    - Return type can be any Python object (primitives, collections, objects, callables)
    - When used as ``@staticmethod``, same parameter constraints apply

**Usage Examples:**
    .. code-block:: python
    
        # ✅ Valid: Zero parameters (static value)
        def database_url() -> str: ...
        
        # ✅ Valid: Single ComponentLoadContext parameter
        def context_table_name(context: ComponentLoadContext) -> str: ...
        
        # ✅ Valid: Returns callable for Jinja2 UDF usage
        def table_generator() -> Callable[[str], str]: ...
        
        # ❌ Invalid: Multiple parameters
        def invalid_multi(context: ComponentLoadContext, other: str) -> str: ...
        
        # ❌ Invalid: Wrong context type
        def invalid_context(context: ComponentDeclLoadContext) -> str: ...

Note:
    While the type alias uses ``Callable[..., Any]`` for compatibility with Python's
    type system (particularly ``staticmethod``), the actual runtime validation enforces
    the strict 0-or-1 parameter constraint documented above.
"""

TEMPLATE_VAR_ATTR = "__dagster_template_var"


@overload
def template_var(fn: TemplateVarFn) -> TemplateVarFn: ...


@overload
def template_var() -> Callable[[TemplateVarFn], TemplateVarFn]: ...


@public
def template_var(
    fn: Optional[TemplateVarFn] = None,
) -> Union[TemplateVarFn, Callable[[TemplateVarFn], TemplateVarFn]]:
    """Decorator that marks a function as a template variable for use in component YAML definitions.

    Template variables provide dynamic values and functions that can be injected into component
    YAML definitions using Jinja2 templating syntax ({{ variable_name }}). They are evaluated
    at component load time and can optionally receive a ComponentLoadContext parameter for
    context-aware behavior.

    These values can be any python object and are passed directly to the component as Python object.
    They can be injected at any level of the defs file.

    There are two main usage patterns:

    1. **Module-level template variables**: Functions defined in a separate module and referenced
       via the ``template_vars_module`` field in component YAML
    2. **Component class static methods**: Template variables defined as ``@staticmethod`` on
       a Component class, automatically available to instances of that component

    Template vars can themselves be functions, in which case they are user-defined functions, invoked
    with function syntax within the defs file.

    Args:
        fn: The function to decorate as a template variable. If None, returns a decorator.

    Returns:
        The decorated function with template variable metadata, or a decorator function.

    Note:
        Template variables are evaluated at component load time, not at runtime. They provide
        configuration values and functions for YAML templating, not runtime component logic.

    Function Signatures:
        Template variable functions can have one of two valid signatures:

        **Zero parameters (static values)**:

        .. code-block:: python

            @dg.template_var
            def static_value() -> Any:
                # Returns a static value computed at load time
                return "computed_value"

        **Single ComponentLoadContext parameter (context-aware)**:

        .. code-block:: python

            @dg.template_var
            def context_value(context: dg.ComponentLoadContext) -> Any:
                # Returns a value based on the component's loading context
                return f"value_{context.path.name}"

        **Return Types:**
        Template variables can return any type, including:

        - **Primitive values**: ``str``, ``int``, ``bool``, ``float``
        - **Collections**: ``list``, ``dict``, ``set``, ``tuple``
        - **Complex objects**: ``PartitionsDefinition``, custom classes, etc.
        - **Functions**: ``Callable`` objects for use as UDFs in Jinja2 templates

        **Invalid Signatures:**

        .. code-block:: python

            # ❌ Multiple parameters not allowed
            @dg.template_var
            def invalid_multiple_params(context: ComponentLoadContext, other_param: str):
                pass

            # ❌ Wrong context type
            @dg.template_var
            def invalid_context_type(context: ComponentDeclLoadContext):
                pass

            # ❌ Static methods with parameters other than context
            class MyComponent(dg.Component):
                @staticmethod
                @dg.template_var
                def invalid_static(param: str):  # Only 0 or 1 (context) params allowed
                    pass

    Examples:
        **Basic template variable (no context needed)**:

        .. code-block:: python

            import dagster as dg
            import os

            @dg.template_var
            def database_url() -> str:
                if os.getenv("ENVIRONMENT") == "prod":
                    return "postgresql://prod-server:5432/db"
                else:
                    return "postgresql://localhost:5432/dev_db"

        **Context-aware template variable**:

        .. code-block:: python

            @dg.template_var
            def component_specific_table(context: dg.ComponentLoadContext) -> str:
                return f"table_{context.path.name}"

        **Template variable returning a function**:

        This is colloquially called a "udf" (user-defined function).

        .. code-block:: python

            @dg.template_var
            def table_name_generator() -> Callable[[str], str]:
                return lambda prefix: f"{prefix}_processed_data"

        **Using template variables in YAML**:

        .. code-block:: yaml

            # defs.yaml
            type: my_project.components.DataProcessor
            template_vars_module: .template_vars
            attributes:
              database_url: "{{ database_url }}"
              table_name: "{{ component_specific_table }}"
              processed_table: "{{ table_name_generator('sales') }}"

        **Component class static methods**:

        .. code-block:: python

            class MyComponent(dg.Component):
                @staticmethod
                @dg.template_var
                def default_config() -> dict:
                    return {"timeout": 30, "retries": 3}

                @staticmethod
                @dg.template_var
                def context_aware_value(context: dg.ComponentLoadContext) -> str:
                    return f"value_for_{context.path.name}"

        **Using in YAML (component static methods)**:

        .. code-block:: yaml

            type: my_project.components.MyComponent
            attributes:
              config: "{{ default_config }}"
              name: "{{ context_aware_value }}"

    See Also:
        - :py:class:`dagster.ComponentLoadContext`: Context object available to template variables
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


def _get_all_static_template_vars(
    cls: type,
) -> Generator[tuple[str, TemplateVarFn, inspect.Signature], None, None]:
    """Helper function to find all staticmethods that are template variables.

    Args:
        cls: The class to search through

    Yields:
        Tuple of (name, func, signature) for each static template variable found
    """
    for name, method in cls.__dict__.items():
        if is_staticmethod(cls, method):
            # Get the actual function from the staticmethod wrapper
            func = method.__get__(None, cls)
            if is_template_var(func):
                sig = inspect.signature(func)
                if len(sig.parameters) > 1:
                    raise ValueError(
                        f"Static template var {name} must have 0 or 1 parameters, got {len(sig.parameters)}"
                    )
                yield name, func, sig


def get_context_free_static_template_vars(cls: type) -> dict[str, TemplateVarFn]:
    """Find all staticmethods in a class that can be used as template variables that do not have a context parameter.
    This is a separate function because of legacy reasons. It is the default implementation of get_additional_scope.

    Args:
        cls: The class to search through

    Returns:
        A dictionary mapping method names to their callable functions for staticmethods that don't require context
    """
    results = {}
    for name, func, sig in _get_all_static_template_vars(cls):
        if len(sig.parameters) == 0:
            results[name] = func()

    return results


def get_context_aware_static_template_vars(
    cls: type, context: "ComponentDeclLoadContext"
) -> dict[str, TemplateVarFn]:
    """Find staticmethods that require context and invoke them with the provided context.

    Args:
        cls: The class to search through
        context: ComponentDeclLoadContext to pass to template variables

    Returns:
        A dictionary mapping method names to their values for context-requiring staticmethods
    """
    results = {}
    for name, func, sig in _get_all_static_template_vars(cls):
        if len(sig.parameters) == 1:
            results[name] = func(context)

    return results
