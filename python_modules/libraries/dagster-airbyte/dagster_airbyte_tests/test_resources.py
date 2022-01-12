import datetime

import pytest
import requests
import responses
from responses import matchers
from responses.matchers import multipart_matcher
from dagster import Failure, build_init_resource_context
from dagster_airbyte import airbyte_resource



@responses.activate
def test_trigger_connection():
    ab_resource = airbyte_resource(
        build_init_resource_context(
            config={
                "host": "some_host",
                "port": "8000",
            }
        )
    )
    
    responses.add(
        method=responses.POST,
        url=ab_resource.api_base_url + "/connections/sync",
        json={"job": {"id": 1 }},
        status=200
    )
    resp = ab_resource.start_sync("some_connection")
    assert resp == {"job": {"id": 1 }}
