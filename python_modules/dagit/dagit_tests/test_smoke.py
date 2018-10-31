import json
from dagit import app
from dagster.cli.dynamic_loader import DynamicObject
from dagster.dagster_examples.repository import define_example_repository


def test_smoke_app():
    repository_container = app.RepositoryContainer(repository=define_example_repository())

    flask_app = app.create_app(repository_container)
    client = flask_app.test_client()

    result = client.post('/graphql', data={'query': 'query { pipelines { name }}'})

    data = json.loads(result.data.decode('utf-8'))

    assert data == {"data": {"pipelines": [{"name": "pandas_hello_world"}]}}
