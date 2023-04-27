class IHasInternalInit:
    """Marker interface which indicates that this class has an internal_init method. All classes with this interface
    are unit tested to ensure that the signature of their internal_init method matches the signature of their
    __init__ method, and that internal_init has no defaults.
    """
