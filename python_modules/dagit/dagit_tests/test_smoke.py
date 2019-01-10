from __future__ import absolute_import, unicode_literals
import json
from dagit import app
from dagit.pipeline_run_storage import PipelineRunStorage
from dagster.tutorials.intro_tutorial.part_six import define_part_six_repo


def test_smoke_app():
    repository_container = app.RepositoryContainer(repository=define_part_six_repo())
    pipeline_run_storage = PipelineRunStorage()
    flask_app = app.create_app(repository_container, pipeline_run_storage)
    client = flask_app.test_client()

    result = client.post('/graphql', data={'query': 'query { pipelines { nodes { name }}}'})

    data = json.loads(result.data.decode('utf-8'))

    assert len(data['data']['pipelines']['nodes']) == 1

    assert set([node_data['name'] for node_data in data['data']['pipelines']['nodes']]) == set(
        ['part_six']
    )
