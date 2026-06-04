"""[lite-engine] Local-filesystem fallback for ``universal_pathlib``.

The full Dagster IO managers use ``upath.UPath`` so a single code path can
target local disk *and* remote object stores (s3://, gs://, ...) via fsspec.
The lite engine only targets the local filesystem, where ``pathlib.Path`` is a
drop-in for ``UPath`` (same ``/``, ``joinpath``, ``exists``, ``mkdir``,
``with_suffix``, ``parts``, ``is_absolute`` surface). When ``upath`` is not
installed we fall back to ``Path`` so the default IO manager keeps working
without pulling in universal-pathlib + fsspec.
"""

import pathlib

try:
    from upath import UPath

    HAS_UPATH = True
except ImportError:
    # Assignment (not a second import) so ruff can't strip it as a redefinition.
    UPath = pathlib.Path
    HAS_UPATH = False
