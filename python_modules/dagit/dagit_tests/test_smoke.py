from __future__ import absolute_import, unicode_literals

import json
from dagster.tutorials.intro_tutorial.repos import define_repo

from dagit import app
from dagster_graphql.implementation.pipeline_run_storage import PipelineRunStorage


def test_smoke_app():
    pipeline_run_storage = PipelineRunStorage()
    flask_app = app.create_app(define_repo(), pipeline_run_storage)
    client = flask_app.test_client()

    result = client.post('/graphql', data={'query': 'query { pipelines { nodes { name }}}'})
    data = json.loads(result.data.decode('utf-8'))
    assert len(data['data']['pipelines']['nodes']) == 1
    assert {node_data['name'] for node_data in data['data']['pipelines']['nodes']} == set(
        ['repo_demo_pipeline']
    )

    result = client.get('/graphql')
    assert result.status_code == 400
    data = json.loads(result.data.decode('utf-8'))
    assert len(data['errors']) == 1
    assert data['errors'][0]['message'] == 'Must provide query string.'

    result = client.get('/dagit/notebook?path=foo.bar')
    assert result.status_code == 400
    assert result.data.decode('utf-8') == 'Invalid Path'

    result = client.post('/graphql', data={'query': 'query { version { slkjd } }'})
    data = json.loads(result.data.decode('utf-8'))
    assert 'errors' in data
    assert len(data['errors']) == 1
    assert 'must not have a sub selection' in data['errors'][0]['message']

    result = client.get('static/foo/bar')
    assert result.status_code == 404
