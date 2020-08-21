from dagster.utils.net import is_local_uri


def test_is_local_uri():
    assert is_local_uri("localhost")
    assert is_local_uri("localhost:80")
    assert is_local_uri("localhost:8080")
    assert is_local_uri("127.0.0.1")
    assert is_local_uri("127.0.0.1:80")
    assert is_local_uri("127.0.0.1:8080")
    assert is_local_uri("0.0.0.0")
    assert is_local_uri("0.0.0.0:80")
    assert is_local_uri("0.0.0.0:8080")

    assert is_local_uri("rpc://")

    assert not is_local_uri("elementl.com")
    assert not is_local_uri("192.0.0.1")
    assert not is_local_uri("http://elementl.com:8080")
    assert not is_local_uri("tcp://elementl.com")
    assert not is_local_uri("hdfs://mycluster.internal")

    assert not is_local_uri("bad.bad")
