from dagster_dlift.client import UnscopedDbtCloudClient
from dagster_dlift.utils import get_job_name
from dlift_kitchen_sink.constants import EXPECTED_TAG


def test_get_models(instance: UnscopedDbtCloudClient, environment_id: int) -> None:
    # Filter to only the models that we use for testing.
    models_response = [
        model for model in instance.get_dbt_models(environment_id) if EXPECTED_TAG in model["tags"]
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


def test_get_sources(instance: UnscopedDbtCloudClient, environment_id: int) -> None:
    """Test that we can get sources from the instance."""
    sources_response = [
        source
        for source in instance.get_dbt_sources(environment_id)
        if EXPECTED_TAG in source["tags"]
    ]
    assert len(sources_response) == 2
    assert {source["uniqueId"] for source in sources_response} == {
        "source.test_environment.jaffle_shop.customers_raw",
        "source.test_environment.jaffle_shop.orders_raw",
    }


def test_get_tests(instance: UnscopedDbtCloudClient, environment_id: int) -> None:
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


def test_cloud_job_apis(
    instance: UnscopedDbtCloudClient, environment_id: int, project_id: int
) -> None:
    """Tests that we can create / destroy a dagster job."""
    job_id = instance.create_job(
        project_id=project_id,
        environment_id=environment_id,
        job_name=get_job_name(environment_id, project_id),
    )
    job_info = instance.get_job_info_by_id(job_id)
    assert job_info["data"]["name"] == get_job_name(environment_id, project_id)
    job_infos = instance.list_jobs(environment_id=environment_id)
    assert job_id in {job_info["id"] for job_info in job_infos}

    response = instance.trigger_job(job_id, steps=["dbt run --select tag:test"])
    run_id = response["data"]["id"]
    run_status = instance.poll_for_run_completion(run_id)
    assert run_status == 10  # Indicates success
    run_results = instance.get_run_results_json(run_id)
    assert {result["unique_id"] for result in run_results["results"]} == {
        "model.test_environment.customers",
        "model.test_environment.stg_customers",
        "model.test_environment.stg_orders",
    }
    instance.destroy_dagster_job(job_id=job_id)
    job_infos = instance.list_jobs(environment_id=environment_id)
    assert job_id not in {job_info["id"] for job_info in job_infos}
