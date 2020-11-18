import pytest
from dagster import seven


@pytest.mark.skipif(seven.IS_WINDOWS, reason="docker doesn't work on windows tests")
def test_ping(docker_grpc_client):
    assert docker_grpc_client.ping("foobar") == "foobar"


@pytest.mark.skipif(seven.IS_WINDOWS, reason="docker doesn't work on windows tests")
def test_streaming(docker_grpc_client):
    results = [
        result for result in docker_grpc_client.streaming_ping(sequence_length=10, echo="foo")
    ]
    assert len(results) == 10
    for sequence_number, result in enumerate(results):
        assert result["sequence_number"] == sequence_number
        assert result["echo"] == "foo"
