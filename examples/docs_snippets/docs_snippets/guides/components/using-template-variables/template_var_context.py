import dagster as dg


@dg.template_var
def simple_value() -> str:
    """No context needed - returns a static value."""
    return "simple_value"


@dg.template_var
def context_aware_value(context: dg.ComponentLoadContext) -> str:
    """Uses context to determine the value."""
    return f"value_for_{context.path.name}"
