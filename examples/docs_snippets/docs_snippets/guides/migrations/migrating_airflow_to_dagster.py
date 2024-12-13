# ruff: isort: skip_file
# ruff: noqa: T201,D415
# type: ignore # problematic imports in example code


def scope_simple_airflow_task():
    import json

    # start_simple_airflow_task
    from airflow.decorators import task

    @task()
    def extract():
        data_string = '{"1001": 301.27, "1002": 433.21, "1003": 502.22}'
        order_data_dict = json.loads(data_string)
        return order_data_dict

    # end_simple_airflow_task


def scope_simple_dagster_asset():
    import json

    # start_simple_dagster_asset
    from dagster import asset

    @asset
    def extract():
        data_string = '{"1001": 301.27, "1002": 433.21, "1003": 502.22}'
        order_data_dict = json.loads(data_string)
        return order_data_dict

    # end_simple_dagster_asset


def scope_full_airflow_example():
    # start_full_airflow_example
    import json

    import pendulum

    from airflow.decorators import dag, task

    @dag(
        schedule=None,
        start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
        catchup=False,
        tags=["example"],
    )
    def tutorial_taskflow_api():
        """### TaskFlow API Tutorial Documentation
        This is a simple data pipeline example which demonstrates the use of
        the TaskFlow API using three simple tasks for Extract, Transform, and Load.
        Documentation that goes along with the Airflow TaskFlow API tutorial is
        located
        [here](https://airflow.apache.org/docs/apache-airflow/stable/tutorial_taskflow_api.html)
        """

        @task
        def extract():
            """#### Extract task
            A simple Extract task to get data ready for the rest of the data
            pipeline. In this case, getting data is simulated by reading from a
            hardcoded JSON string.
            """
            data_string = '{"1001": 301.27, "1002": 433.21, "1003": 502.22}'

            order_data_dict = json.loads(data_string)
            return order_data_dict

        @task(multiple_outputs=True)
        def transform(order_data_dict: dict):
            """#### Transform task
            A simple Transform task which takes in the collection of order data and
            computes the total order value.
            """
            total_order_value = 0

            for value in order_data_dict.values():
                total_order_value += value

            return {"total_order_value": total_order_value}

        @task
        def load(total_order_value: float):
            """#### Load task
            A simple Load task which takes in the result of the Transform task and
            instead of saving it to end user review, just prints it out.
            """
            print(f"Total order value is: {total_order_value:.2f}")

        order_data = extract()
        order_summary = transform(order_data)
        load(order_summary["total_order_value"])

    tutorial_taskflow_api()

    # end_full_airflow_example


def scope_full_dagster_example():
    # start_full_dagster_example
    import json

    from dagster import AssetExecutionContext, Definitions, define_asset_job, asset

    @asset
    def extract():
        """Extract task

        A simple Extract task to get data ready for the rest of the data pipeline. In this case, getting
        data is simulated by reading from a hardcoded JSON string.
        """
        data_string = '{"1001": 301.27, "1002": 433.21, "1003": 502.22}'

        order_data_dict = json.loads(data_string)

        return order_data_dict

    @asset
    def transform(extract):
        """Transform task

        A simple Transform task which takes in the collection of order data and computes the total order
        value.
        """
        total_order_value = 0

        for value in extract.values():
            total_order_value += value

        return total_order_value

    @asset
    def load(context: AssetExecutionContext, transform):
        """Load task

        A simple Load task which takes in the result of the Transform task and instead of saving it to
        end user review, just prints it out.
        """
        context.log.info(f"Total order value is: {transform:.2f}")

    airflow_taskflow_example = define_asset_job(
        name="airflow_taskflow_example", selection=[extract, transform, load]
    )

    defs = Definitions(
        assets=[extract, transform, load], jobs=[airflow_taskflow_example]
    )

    # end_full_dagster_example


def scope_run_docker_image_with_airflow():
    # start_run_docker_image_with_airflow
    from airflow import DAG
    from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
        KubernetesPodOperator,
    )
    from pendulum import datetime

    with DAG(
        dag_id="example_kubernetes_dag", schedule_interval=None, catchup=False
    ) as dag:
        KubernetesPodOperator(
            image="example-data-pipeline:latest",
            name="example-kubernetes-task",
            task_id="example-kubernetes-task",
            get_logs=True,
        )

    # end_run_docker_image_with_airflow


def scope_run_docker_image_with_dagster_pipes():
    # start_run_docker_image_with_dagster_pipes
    from dagster import AssetExecutionContext, asset
    from dagster_k8s import PipesK8sClient

    @asset
    def k8s_pipes_asset(
        context: AssetExecutionContext, k8s_pipes_client: PipesK8sClient
    ):
        return k8s_pipes_client.run(
            context=context,
            image="example-data-pipeline:latest",
            base_pod_spec={
                "containers": [
                    {
                        "name": "data-processing-rs",
                        "image": "data-processing-rs",
                    }
                ]
            },
        ).get_materialize_result()

    # end_run_docker_image_with_dagster_pipes
