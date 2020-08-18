class LakehouseError(Exception):
    """Base class for all errors thrown by the Lakehouse framework."""


class LakehouseLoadingError(LakehouseError):
    """Indicates that there was trouble loading a Lakehouse definition."""


class LakehouseAssetQueryError(LakehouseError):
    """Indicates that a bad query string was provided when querying for assets."""
