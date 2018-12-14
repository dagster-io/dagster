from __future__ import absolute_import
import json
from dagit import app
from dagit.pipeline_run_storage import PipelineRunStorage
from dagster_contrib.dagster_examples.repository import define_example_repository


def test_smoke_app():
    repository_container = app.RepositoryContainer(repository=define_example_repository())
    pipeline_run_storage = PipelineRunStorage()
    flask_app = app.create_app(repository_container, pipeline_run_storage)
    client = flask_app.test_client()

    result = client.post('/graphql', data={'query': 'query { pipelines { nodes { name }}}'})

    data = json.loads(result.data.decode('utf-8'))

    assert data == {"data": {"pipelines": {"nodes": [{"name": "pandas_hello_world"}]}}}
