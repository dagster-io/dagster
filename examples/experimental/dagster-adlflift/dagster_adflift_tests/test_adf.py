import json
import os
import time
from collections import defaultdict

import requests
from azure.identity import ClientSecretCredential
from dagster import AssetSpec, multi_asset


def get_authenticated_session() -> requests.Session:
    credential = ClientSecretCredential(
        tenant_id=os.environ["TEST_AZURE_TENANT_ID"],
        client_id=os.environ["TEST_AZURE_CLIENT_ID"],
        client_secret=os.environ["TEST_AZURE_CLIENT_SECRET"],
    )
    access_token = credential.get_token("https://management.azure.com/.default")
    headers = {"Authorization": f"Bearer {access_token.token}", "Content-Type": "application/json"}
    session = requests.Session()
    session.headers.update(headers)
    return session


def make_azure_request(endpoint, method, data=None) -> dict:
    return (
        get_authenticated_session()
        .request(method=method, url=endpoint, data=json.dumps(data) if data else None)
        .json()
    )


def test_azure_request() -> None:
    subscription_id = "84120269-35b6-461c-97ae-83683bc08584"
    resource_group = "chris-adf-test"
    factory_name = "datafactorylusgmsnnyyajq"
    url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.DataFactory/factories/{factory_name}/pipelines?api-version=2018-06-01"
    response = make_azure_request(url, "GET")
    pipelines_response = response["value"]
    deps = defaultdict(set)  # dependencies between datasets
    all_refs = set()
    datasets_per_pipeline = defaultdict(set)
    for pipeline in pipelines_response:
        for activity in pipeline["properties"]["activities"]:
            input_refs = [inp["referenceName"] for inp in activity["inputs"]]
            output_refs = [out["referenceName"] for out in activity["outputs"]]
            datasets_per_pipeline[pipeline["name"]].update(input_refs + output_refs)
            all_refs.update(input_refs + output_refs)
            for output_ref in output_refs:
                deps[output_ref].update(input_refs)
    url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.DataFactory/factories/{factory_name}/datasets?api-version=2018-06-01"
    response = make_azure_request(url, "GET")["value"]
    datasets = response[0]
    for dataset in datasets:
        name = dataset["name"]  # this would become asset key
        location_type = dataset["properties"]["typeProperties"]["location"][
            "type"
        ]  # this would become kind
        deps_for_dataset = deps[name]  # asset deps

    # We'll now create a multi asset for each pipeline.
    assets = []
    for pipeline, datasets in datasets_per_pipeline.items():

        @multi_asset(
            specs=[AssetSpec(key=dataset, kind=..., deps=deps[dataset]) for dataset in datasets]
        )
        def trigger_pipeline():
            url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.DataFactory/factories/{factory_name}/pipelines/{pipeline}/createRun?api-version=2018-06-01"
            run_id = make_azure_request(url, "POST")["runId"]
            start_time = time.time()
            while time.time() - start_time < 300:
                url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.DataFactory/factories/{factory_name}/pipelines/{pipeline}/runs/{run_id}?api-version=2018-06-01"
                run_status = make_azure_request(url, "GET")["status"]
                if run_status == "InProgress":
                    time.sleep(5)
                elif run_status == "Succeeded":
                    break
                else:
                    raise Exception(f"Pipeline run failed with status {run_status}")
            raise Exception("Pipeline run did not complete in 5 minutes")

        assets.append(trigger_pipeline)
