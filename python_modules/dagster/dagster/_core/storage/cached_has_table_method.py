from collections.abc import Callable
from functools import wraps
from typing import TypeVar

T_Storage = TypeVar("T_Storage")


CACHED_HAS_TABLE_METHOD_CACHE_FIELD = "_cached_has_table_method_cache__internal__"


def cached_has_table_method(
    has_table_method: Callable[[T_Storage, str], bool],
) -> Callable[[T_Storage, str], bool]:
    """Cache True results of the Storage class ``has_table(self, table_name: str) -> bool`` method.

    Can only be used once per class. The internal cache is keyed only by table name, not by method
    name, so two decorated methods on the same class would share a cache.

    Usage:

        .. code-block:: python

            class Storage:
                @cached_has_table_method
                def has_table(self, table_name: str) -> bool:
                    ...

            storage = Storage()
            assert storage.has_table("existing_table")  # compute value and cache the True result
            assert storage.has_table("existing_table")  # return cached True
            if not storage.has_table("new_table"):
                do_upgrade_migration()
            assert storage.has_table("new_table") is True   # re-compute value, cache the new True
            assert storage.has_table("new_table") is True   # return cached True

    Intended for use when:
        - There is any chance that the method might be called frequently; AND
        - There is an assumption that table names passed to the method will not be DROPed.

    This prevents frequent and useless schema-introspection calls to
    ``db.inspect(conn).get_table_names()``, which in turn prevents frequent and useless database
    queries on hot paths. On postgres, ``get_table_names()`` expands to

        .. code-block:: sql

            SELECT pg_catalog.pg_class.relname FROM pg_catalog.pg_class JOIN pg_catalog.pg_namespace
            ON pg_catalog.pg_namespace.oid = pg_catalog.pg_class.relnamespace WHERE
            pg_catalog.pg_class.relkind = ANY (ARRAY['r', 'p']) AND
            pg_catalog.pg_class.relpersistence != 't' AND
            pg_catalog.pg_table_is_visible(pg_catalog.pg_class.oid) AND
            pg_catalog.pg_namespace.nspname != 'pg_catalog'
    """

    @wraps(has_table_method)
    def _cached_has_table_method_wrapper(self: T_Storage, table_name: str) -> bool:
        if not hasattr(self, CACHED_HAS_TABLE_METHOD_CACHE_FIELD):
            setattr(self, CACHED_HAS_TABLE_METHOD_CACHE_FIELD, {})

        cache: dict[str, bool] = getattr(self, CACHED_HAS_TABLE_METHOD_CACHE_FIELD)

        if table_name in cache:
            return cache[table_name]
        result = has_table_method(self, table_name)
        if result:
            cache[table_name] = result
        return result

    return _cached_has_table_method_wrapper
