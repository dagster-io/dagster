from dagster.grpc.client import DagsterGrpcClient


def test_ping(grpc_server):
    grpc_host, grpc_port = grpc_server
    assert DagsterGrpcClient(port=grpc_port, host=grpc_host).ping('foobar') == 'foobar'


def test_streaming(grpc_server):
    grpc_host, grpc_port = grpc_server
    api_client = DagsterGrpcClient(port=grpc_port, host=grpc_host)
    results = [result for result in api_client.streaming_ping(sequence_length=10, echo='foo')]
    assert len(results) == 10
    for sequence_number, result in enumerate(results):
        assert result['sequence_number'] == sequence_number
        assert result['echo'] == 'foo'
