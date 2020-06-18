from __future__ import absolute_import, unicode_literals

import json

from dagit import app

from dagster.cli.workspace import get_workspace_from_kwargs
from dagster.core.instance import DagsterInstance

SMOKE_TEST_QUERY = '''
{
    repositoriesOrError {
        ... on PythonError {
            message
            stack
        }
        ... on RepositoryConnection {
            nodes {
                pipelines {
                    name
                }
            }
        }
    }
}
'''

# https://github.com/dagster-io/dagster/issues/2623
def test_smoke_app():
    flask_app = app.create_app_from_workspace(
        get_workspace_from_kwargs(
            dict(
                module_name='docs_snippets.intro_tutorial.advanced.repositories.repos',
                definition='hello_cereal_repository',
            )
        ),
        DagsterInstance.ephemeral(),
    )
    client = flask_app.test_client()

    result = client.post('/graphql', data={'query': SMOKE_TEST_QUERY},)
    data = json.loads(result.data.decode('utf-8'))
    assert len(data['data']['repositoriesOrError']['nodes']) == 1
    assert len(data['data']['repositoriesOrError']['nodes'][0]['pipelines']) == 2
    assert {
        node_data['name']
        for node_data in data['data']['repositoriesOrError']['nodes'][0]['pipelines']
    } == set(['hello_cereal_pipeline', 'complex_pipeline'])

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

    # Missing routes return the index.html file of the Dagit react app, so the user
    # gets our UI when they navigate to "synthetic" react router URLs.
    result = client.get('static/foo/bar')
    assert result.status_code == 200
    assert "You need to enable JavaScript to run this app." in result.data.decode('utf-8')

    result = client.get('pipelines/foo')
    assert result.status_code == 200
    assert "You need to enable JavaScript to run this app." in result.data.decode('utf-8')
