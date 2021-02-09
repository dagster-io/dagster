import inspect
import sys

import pytest
from dagster import check
from dagster.core.test_utils import ExplodingRunLauncher

from .graphql_context_test_suite import GraphQLContextVariant, manage_graphql_context


@pytest.mark.graphql_context_variants
@pytest.mark.parametrize("variant", GraphQLContextVariant.all_readonly_variants())
def test_readonly_variants(variant):
    # Note: This mark is only run in the `tox_postgres.ini` file and not the default `tox.ini`
    # file because 3 of the variants have a postgres dependency
    assert isinstance(variant, GraphQLContextVariant)
    with manage_graphql_context(variant) as context:
        assert isinstance(context.instance.run_launcher, ExplodingRunLauncher)


def get_all_static_functions(klass):
    check.invariant(sys.version_info >= (3,))

    def _yield_all():
        for attr_name in dir(klass):
            attr = inspect.getattr_static(klass, attr_name)
            if isinstance(attr, staticmethod):
                # the actual function is on the __func__ property
                yield attr.__func__

    return list(_yield_all())


def test_get_all_static_members():
    class Bar:
        class_var = "foo"

        @staticmethod
        def static_one():
            pass

        @staticmethod
        def static_two():
            pass

        @classmethod
        def classthing(cls):
            pass

    assert set(get_all_static_functions(Bar)) == {Bar.static_one, Bar.static_two}


def test_all_variants_in_variants_function():
    """
    This grabs all pre-defined variants on GraphQLContextVariant (defined as static methods that
    return a single ContextVariant) and tests two things:
    1) They all contain a unique test_id
    2) That the all_variants() static method returns *all* of them
    """

    variant_test_ids_declared_on_class = set()
    for static_function in get_all_static_functions(GraphQLContextVariant):
        maybe_variant = static_function()
        if isinstance(maybe_variant, GraphQLContextVariant):
            assert maybe_variant.test_id
            assert maybe_variant.test_id not in variant_test_ids_declared_on_class
            variant_test_ids_declared_on_class.add(maybe_variant.test_id)

    test_ids_returned_by_all_variants = {
        var.test_id for var in GraphQLContextVariant.all_variants()
    }

    assert test_ids_returned_by_all_variants == variant_test_ids_declared_on_class


def test_readonly_marks_filter():
    readonly_test_ids = {
        var.test_id
        for var in [
            GraphQLContextVariant.readonly_in_memory_instance_in_process_env(),
            GraphQLContextVariant.readonly_in_memory_instance_lazy_repository(),
            GraphQLContextVariant.readonly_in_memory_instance_multi_location(),
            GraphQLContextVariant.readonly_in_memory_instance_managed_grpc_env(),
            GraphQLContextVariant.readonly_sqlite_instance_in_process_env(),
            GraphQLContextVariant.readonly_sqlite_instance_lazy_repository(),
            GraphQLContextVariant.readonly_sqlite_instance_multi_location(),
            GraphQLContextVariant.readonly_sqlite_instance_managed_grpc_env(),
            GraphQLContextVariant.readonly_sqlite_instance_deployed_grpc_env(),
            GraphQLContextVariant.readonly_postgres_instance_in_process_env(),
            GraphQLContextVariant.readonly_postgres_instance_lazy_repository(),
            GraphQLContextVariant.readonly_postgres_instance_multi_location(),
            GraphQLContextVariant.readonly_postgres_instance_managed_grpc_env(),
        ]
    }

    assert {
        var.test_id for var in GraphQLContextVariant.all_readonly_variants()
    } == readonly_test_ids
