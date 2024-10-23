from typing import Any


class IHasInternalInit:
    """Marker interface which indicates that this class has an dagster_internal_init method. All classes with this interface
    are unit tested to ensure that the signature of their dagster_internal_init method matches the signature of their
    __init__ method, and that dagster_internal_init has no defaults.
    """

    @staticmethod
    def dagster_internal_init(*args: Any, **kwargs: Any) -> object:
        """This method is called by the __init__ method of subclasses of IHasInternalInit. It is not intended to be called
        directly.
        """
        raise NotImplementedError(
            "This method is called by the __init__ method of subclasses of IHasInternalInit. It is not intended to be called directly."
        )
