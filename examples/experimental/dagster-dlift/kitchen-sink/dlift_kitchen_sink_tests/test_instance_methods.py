from dlift_kitchen_sink.constants import EXPECTED_TAG, TEST_ENV_NAME
from dlift_kitchen_sink.instance import get_instance


def test_get_models() -> None:
    env_id = get_instance().get_environment_id_by_name(TEST_ENV_NAME)
    # Filter to only the models that we use for testing.
    models_response = [
        model for model in get_instance().get_dbt_models(env_id) if EXPECTED_TAG in model["tags"]
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


def test_get_sources() -> None:
    """Test that we can get sources from the instance."""
    env_id = get_instance().get_environment_id_by_name(TEST_ENV_NAME)
    sources_response = [
        source
        for source in get_instance().get_dbt_sources(env_id)
        if EXPECTED_TAG in source["tags"]
    ]
    assert len(sources_response) == 2
    assert {source["uniqueId"] for source in sources_response} == {
        "source.test_environment.jaffle_shop.customers_raw",
        "source.test_environment.jaffle_shop.orders_raw",
    }
