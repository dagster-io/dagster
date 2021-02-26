from collections import OrderedDict

from dagster import check
from dagster.seven import funcsigs

from .asset import Asset
from .computation import AssetDependency, Computation
from .table import Table


def computed_asset(storage_key="default_storage", path=None, input_assets=None, version=None):
    """Create an Asset with its computation built from the decorated function.

    The type annotations on the arguments and return value of the decorated function are use to
    determine which TypeStoragePolicy will be used to load and save its outputs and inputs.

    Args:
        storage_key (str): The key of the storage used to persist the asset. Defaults to
            "default_storage".
        path (Optional[Tuple[str, ...]]): The path of the asset within the storage_key. If not
            given, the name of the decorated function is used.
        input_assets (Optional[Union[List[Asset], Dict[str, Asset]]]): The assets that this asset
            depends on, mapped to the arguments of the decorated function.  If a dictionary is
            passed, the keys should be the same as the names of the decorated function's arguments.
            If a list is passed, the first asset in the list is mapped to the first argument of the
            decorated function, and so on.
        version (Optional[str]): The version of the asset's computation.  Two assets should have
            the same version if and only if their computations deterministically produce the same
            outputs when provided the same inputs.

    Examples:

        .. code-block:: python

            @computed_asset(storage_key='filesystem', input_assets=[orders_asset])
            def asia_orders_asset(orders: pyspark.sql.DataFrame) -> pyspark.sql.DataFrame:
                return orders.filter(orders['continent'] == 'asia')

            @computed_asset(storage_key='filesystem', input_assets={'orders': orders_asset})
            def asia_orders_asset(orders: pyspark.sql.DataFrame) -> pyspark.sql.DataFrame:
                return orders.filter(orders['continent'] == 'asia')

            @computed_asset(storage_key='filesystem', input_assets=[orders_asset, users_asset])
            def user_orders_asset(
                orders: pyspark.sql.DataFrame, users: pyspark.sql.DataFrame
            ) -> pyspark.sql.DataFrame:
                return orders.join(users, 'user_id')

            @computed_asset(storage_key='filesystem', input_assets=[orders_asset])
            def orders_count_asset(orders: pyspark.sql.DataFrame) -> int:
                return orders.count()

            @computed_asset(storage_key='filesystem')
            def one_asset() -> int:
                return 1

    """

    def _computed_asset(fn):
        _path = path or (fn.__name__,)
        _input_assets = input_assets or []
        kwarg_deps = _deps_by_arg_name(_input_assets, fn)

        return Asset(
            storage_key=storage_key,
            path=_path,
            computation=Computation(
                compute_fn=fn,
                deps=kwarg_deps,
                output_in_memory_type=_infer_output_type(fn),
                version=version,
            ),
        )

    return _computed_asset


def computed_table(
    storage_key="default_storage", path=None, input_assets=None, columns=None, version=None
):
    """Create a Table with its computation built from the decorated function.

    The type annotations on the arguments and return value of the decorated function are use to
    determine which TypeStoragePolicy will be used to load and save its outputs and inputs.

    Args:
        storage_key (str): The key of the storage used to persist the asset. Defaults to
            "default_storage".
        path (Optional[Tuple[str, ...]]): The path of the asset within the storage_key. If not
            given, the name of the decorated function is used.
        input_assets (Optional[Union[List[Asset], Dict[str, Asset]]]): The assets that this asset
            depends on, mapped to the arguments of the decorated function.  If a dictionary is
            passed, the keys should be the same as the names of the decorated function's arguments.
            If a list is passed, the first asset in the list is mapped to the first argument of the
            decorated function, and so on.
        columns (Optional[List[Column]]): The table's columns.
        version (Optional[str]): The version of the table's computation. Two tables should have
            the same version if and only if their computations deterministically produce the same
            outputs when provided the same inputs.
    """

    def _computed_table(fn):
        _path = path or (fn.__name__,)
        _input_assets = input_assets or []
        kwarg_deps = _deps_by_arg_name(_input_assets, fn)

        return Table(
            storage_key=storage_key,
            path=_path,
            computation=Computation(
                compute_fn=fn,
                deps=kwarg_deps,
                output_in_memory_type=_infer_output_type(fn),
                version=version,
            ),
            columns=columns,
        )

    return _computed_table


def _deps_by_arg_name(input_assets, fn):
    """
    Args:
        input_assets (Optional[Union[List[Asset], Dict[str, Asset]]])
        fn (Callable)

    Returns (Dict[str, AssetDependency])
    """
    kwarg_types = _infer_kwarg_types(fn)
    if isinstance(input_assets, list):
        check.invariant(
            len(kwarg_types) == len(input_assets),
            'For {fn_name}, input_assets length "{input_assets_len}"" must match number of '
            'keyword args "{num_kwargs}"'.format(
                fn_name=fn.__name__,
                input_assets_len=len(input_assets),
                num_kwargs=len(kwarg_types),
            ),
        )
        return {
            kwarg: AssetDependency(input_asset, kwarg_types[kwarg])
            for kwarg, input_asset in zip(kwarg_types.keys(), input_assets)
        }
    elif isinstance(input_assets, dict):
        check.invariant(
            kwarg_types.keys() == input_assets.keys(),
            "input_assets keys {kwarg_deps_keys} must match keyword args {kwargs}".format(
                kwarg_deps_keys=input_assets.keys(),
                kwargs=kwarg_types.keys(),
            ),
        )
        return {
            kwarg: AssetDependency(input_assets[kwarg], kwarg_types[kwarg])
            for kwarg in kwarg_types.keys()
        }
    else:
        check.failed("input_assets must be a list or a dict")


def _infer_kwarg_types(fn):
    signature = funcsigs.signature(fn)
    params = signature.parameters.values()
    return OrderedDict((param.name, param.annotation) for param in params)


def _infer_output_type(fn):
    signature = funcsigs.signature(fn)
    return signature.return_annotation
