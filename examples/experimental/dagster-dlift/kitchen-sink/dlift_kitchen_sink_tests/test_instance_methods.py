from dagster_dlift.client import DbtCloudClient
from dlift_kitchen_sink.constants import EXPECTED_TAG
from dlift_kitchen_sink.instance import get_instance


def test_get_models(instance: DbtCloudClient, environment_id: int) -> None:
    # Filter to only the models that we use for testing.
    models_response = [
        model
        for model in get_instance().get_dbt_models(environment_id)
        if EXPECTED_TAG in model["tags"]
    ]

    assert len(models_response) == 3
    customers = next(
        iter(
            [
                model
                for model in models_response
                if model["uniqueId"] == "model.test_environment.customers"
            ]
        )
    )
    assert len(customers["parents"]) == 2
    assert {parent["uniqueId"] for parent in customers["parents"]} == {
        "model.test_environment.stg_customers",
        "model.test_environment.stg_orders",
    }
    stg_customers = next(
        iter(
            [
                model
                for model in models_response
                if model["uniqueId"] == "model.test_environment.stg_customers"
            ]
        )
    )
    assert len(stg_customers["parents"]) == 1
    assert {parent["uniqueId"] for parent in stg_customers["parents"]} == {
        "source.test_environment.jaffle_shop.customers_raw"
    }
    stg_orders = next(
        iter(
            [
                model
                for model in models_response
                if model["uniqueId"] == "model.test_environment.stg_orders"
            ]
        )
    )
    assert len(stg_orders["parents"]) == 1
    assert {parent["uniqueId"] for parent in stg_orders["parents"]} == {
        "source.test_environment.jaffle_shop.orders_raw"
    }


def test_get_sources(instance: DbtCloudClient, environment_id: int) -> None:
    """Test that we can get sources from the instance."""
    sources_response = [
        source
        for source in get_instance().get_dbt_sources(environment_id)
        if EXPECTED_TAG in source["tags"]
    ]
    assert len(sources_response) == 2
    assert {source["uniqueId"] for source in sources_response} == {
        "source.test_environment.jaffle_shop.customers_raw",
        "source.test_environment.jaffle_shop.orders_raw",
    }


def test_get_tests(instance: DbtCloudClient, environment_id: int) -> None:
    """Test that we can get tests from the instance."""
    tests_response = [
        test for test in instance.get_dbt_tests(environment_id) if EXPECTED_TAG in test["tags"]
    ]
    assert {test["name"] for test in tests_response} == {
        "accepted_values_stg_orders_status__placed__shipped__completed__return_pending__returned",
        "not_null_customers_customer_id",
        "not_null_stg_customers_customer_id",
        "not_null_stg_orders_customer_id",
        "not_null_stg_orders_order_id",
        "relationships_stg_orders_customer_id__customer_id__ref_stg_customers_",
        "unique_customers_customer_id",
        "unique_stg_customers_customer_id",
        "unique_stg_orders_order_id",
    }
