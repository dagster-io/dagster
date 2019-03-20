from __future__ import absolute_import, unicode_literals

from dagster.seven import json_ as json
from dagster.tutorials.intro_tutorial.repos import define_repo

from dagit import app
from dagit.pipeline_run_storage import PipelineRunStorage


def test_smoke_app():
    repository_container = app.RepositoryContainer(repository=define_repo())
    pipeline_run_storage = PipelineRunStorage()
    flask_app = app.create_app(repository_container, pipeline_run_storage)
    client = flask_app.test_client()

    result = client.post('/graphql', data={'query': 'query { pipelines { nodes { name }}}'})

    data = json.loads(result.data.decode('utf-8'))

    assert len(data['data']['pipelines']['nodes']) == 1

    assert {node_data['name'] for node_data in data['data']['pipelines']['nodes']} == set(
        ['repo_demo_pipeline']
    )
