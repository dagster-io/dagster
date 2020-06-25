import pytest
import responses
from requests.exceptions import HTTPError
from dagster_dynatrace import DTClient

@pytest.fixture
def shared_client():
    client = DTClient('dt_token', 'http://host_name')

    yield client


def test_build_url(shared_client: DTClient):
    assert shared_client.build_url('test') == 'http://host_name/api/v2/test'
    assert shared_client.build_url_v1('test') == 'http://host_name/api/v1/test'


def test_build_headers(shared_client: DTClient):
    assert 'dt_token' in shared_client.build_headers().get('Authorization')


@responses.activate
def test_push(shared_client: DTClient):
    responses.add(
        responses.POST,
        'http://host_name/api/v2/push_here',
        json={'linesOk': 1},
        status=200,
    )

    resp = shared_client.push('visitors.unique,browser=ie11 99', 'push_here')

    assert resp['linesOk'] == 1
    assert responses.calls[0].request.body == 'visitors.unique,browser=ie11 99'


@responses.activate
def test_push_with_error(shared_client: DTClient):
    responses.add(
        responses.POST,
        'http://host_name/api/v2/push_here',
        status=500,
    )

    with pytest.raises(HTTPError):
        shared_client.push('visitors.unique,browser=ie11 99', 'push_here')


@responses.activate
def test_pull(shared_client: DTClient):
    responses.add(
        responses.GET,
        'http://host_name/api/v2/pull_here',
        json={'linesOk': 1},
        status=200,
    )

    resp = shared_client.pull('one', 'pull_here')
    shared_client.pull(['one', 'two'], 'pull_here')
    shared_client.pull('one,two,three', 'pull_here')

    assert resp['linesOk'] == 1
    assert responses.calls[0].request.params == {'metricSelector': 'one'}
    assert responses.calls[1].request.params == {'metricSelector': 'one,two'}
    assert responses.calls[2].request.params == {'metricSelector': 'one,two,three'}


@responses.activate
def test_pull_with_error(shared_client: DTClient):
    responses.add(
        responses.GET,
        'http://host_name/api/v2/pull_here',
        status=500,
    )

    with pytest.raises(HTTPError):
        shared_client.pull('one', 'pull_here')
