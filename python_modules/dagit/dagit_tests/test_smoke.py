from __future__ import absolute_import, unicode_literals

import json

from dagit import app

from dagster import ExecutionTargetHandle
from dagster.core.instance import DagsterInstance


def test_smoke_app():
    flask_app = app.create_app(
        ExecutionTargetHandle.for_repo_module(
            module_name='dagster_examples.intro_tutorial.repos', fn_name='define_repo'
        ),
        DagsterInstance.ephemeral(),
    )
    client = flask_app.test_client()

    result = client.post('/graphql', data={'query': 'query { pipelines { nodes { name }}}'})
    data = json.loads(result.data.decode('utf-8'))
    assert len(data['data']['pipelines']['nodes']) == 2
    assert {node_data['name'] for node_data in data['data']['pipelines']['nodes']} == set(
        ['hello_cereal_pipeline', 'complex_pipeline']
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

    result = client.get('vendor/foo/bar')
    assert result.status_code == 404
