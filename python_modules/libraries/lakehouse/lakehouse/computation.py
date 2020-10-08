from collections import namedtuple

from dagster import check


class AssetDependency(namedtuple("_AssetDependency", "asset in_memory_type")):
    """An asset dependency describes how the contents of another asset are provided to a
    Computation's compute_fn.

    Attributes:
        asset (Asset): The asset that we depend on.
        in_memory_type (Type): The type, e.g. pandas.DataFrame, that the asset's contents should be
            hydrated into to be passed as the compute_fn.
    """


class Computation(namedtuple("_Computation", "compute_fn deps output_in_memory_type version")):
    """A description of the computation responsible for producing an asset.

    E.g. a SQL select statement or python code that trains an ML model.

    The computation is agnostic to the physical details of where it's stored and how it's saved to
    and loaded from that storage. The Lakehouse that the asset resides in is responsible for
    those.

    Attributes:
        compute_fn (Callable): A python function with no side effects that produces an in-memory
            representation of the asset's contents from in-memory representation of the
            asset' inputs.
        deps (Dict[str, AssetDependency]): The assets that the compute_fn depends on
            to produce the asset's contents, keyed by their arg names in the compute_fn
            definition.
        output_in_memory_type (Type): The python type that the compute_fn will return.
        version (Optional[str]): The version of the computation. Two computations should have
            the same version if and only if they deterministically produce the same outputs when
            provided the same inputs.
    """

    def __new__(cls, compute_fn, deps, output_in_memory_type, version):
        return super(Computation, cls).__new__(
            cls,
            compute_fn=check.callable_param(compute_fn, "compute_fn"),
            deps=check.dict_param(deps, "deps", key_type=str, value_type=AssetDependency),
            output_in_memory_type=check.inst_param(
                output_in_memory_type, "output_in_memory_type", type
            ),
            version=version,
        )
