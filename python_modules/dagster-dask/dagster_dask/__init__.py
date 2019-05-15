from .version import __version__

from .config import DaskConfig
from .execute import execute_on_dask

__all__ = ['execute_on_dask', 'DaskConfig']
