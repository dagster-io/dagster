import threading
import time

import grpc
from dagster.grpc.client import ephemeral_grpc_api_client


def _stream_events_target(results, api_client):
    for result in api_client.streaming_ping(sequence_length=10000, echo="foo"):
        results.append(result)


def test_streaming_terminate():
    with ephemeral_grpc_api_client() as api_client:
        streaming_results = []
        stream_events_result_thread = threading.Thread(
            target=_stream_events_target, args=[streaming_results, api_client]
        )
        stream_events_result_thread.daemon = True
        stream_events_result_thread.start()

        start = time.time()
        while not streaming_results:
            if time.time() - start > 15:
                raise Exception("Timed out waiting for streaming results")

            time.sleep(0.001)

        try:
            api_client.shutdown_server()
        except grpc._channel._InactiveRpcError:  # pylint: disable=protected-access
            # shutting down sometimes happens so fast that it terminates the calling RPC
            pass

        stream_events_result_thread.join(timeout=90)

        assert not stream_events_result_thread.is_alive()
        assert len(streaming_results) == 10000

        api_client._server_process.wait()  # pylint: disable=protected-access
        assert api_client._server_process.poll() == 0  # pylint: disable=protected-access
