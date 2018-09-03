import json
from dagit import app
from dagster.cli.repository_config import RepositoryInfo
from dagster.dagster_examples.repository import define_example_repository


def test_smoke_app():
    repository_container = app.RepositoryContainer(
        RepositoryInfo(
            repository=define_example_repository(),
            module=None,
            fn_name=None,
            fn=None,
            module_name=None,
        )
    )

    flask_app = app.create_app(repository_container)
    client = flask_app.test_client()

    result = client.post('/graphql', data={'query': 'query { pipelines { name }}'})

    data = json.loads(result.data)

    assert data == {"data": {"pipelines": [{"name": "pandas_hello_world"}]}}
