from __future__ import absolute_import, unicode_literals

import json

from dagit import app

from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.instance import DagsterInstance

SMOKE_TEST_QUERY = '''
{
    repositoryLocationsOrError {
        ... on PythonError {
            message
            stack
        }
        ... on RepositoryLocationConnection {
            nodes {
                repositories {
                    pipelines {
                        name
                    }
                }
            }
        }
    }
}
'''


def test_smoke_app():
    flask_app = app.create_app_with_reconstructable_repo(
        ReconstructableRepository.for_module(
            module='dagster_examples.intro_tutorial.repos', fn_name='hello_cereal_repository'
        ),
        DagsterInstance.ephemeral(),
    )
    client = flask_app.test_client()

    result = client.post('/graphql', data={'query': SMOKE_TEST_QUERY},)
    data = json.loads(result.data.decode('utf-8'))
    assert len(data['data']['repositoryLocationsOrError']['nodes']) == 1
    assert len(data['data']['repositoryLocationsOrError']['nodes'][0]['repositories']) == 1
    assert (
        len(data['data']['repositoryLocationsOrError']['nodes'][0]['repositories'][0]['pipelines'])
        == 2
    )
    assert {
        node_data['name']
        for node_data in data['data']['repositoryLocationsOrError']['nodes'][0]['repositories'][0][
            'pipelines'
        ]
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
