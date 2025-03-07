import inspect
from functools import wraps
from typing import Callable


# Decorator definition
def udf(func: Callable) -> Callable:
    """Decorator that validates a function is a staticmethod and marks it as a udf."""
    # Mark the function as a udf by adding an attribute
    setattr(func, "__is_udf__", True)

    # Get the original function and preserve its metadata
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return staticmethod(wrapper)  # type:ignore something about staticmethod


# Function to collect udf-decorated static methods
def get_udf_methods(cls: type) -> dict[str, Callable]:
    """Returns a dictionary of udf-decorated static methods from a class.
    Key is the function name, value is the function itself.
    """
    udf_methods = {}

    members = inspect.getmembers(cls)

    # Iterate through all class attributes
    for name, attr in members:
        # Check if it's a staticmethod
        # Get the original function using __get__ to access the underlying function
        if isinstance(attr, staticmethod):
            func = attr.__get__(None, cls)
            # Check if it has our udf marker
            if getattr(func, "__is_udf__", False):
                udf_methods[name] = func

    return udf_methods
