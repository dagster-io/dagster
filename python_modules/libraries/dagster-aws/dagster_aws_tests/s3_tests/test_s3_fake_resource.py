from dagster_aws.s3 import create_s3_fake_resource


def test_put_object(tmp_path):
    s3 = create_s3_fake_resource()

    s3.put_object(Bucket="test", Key="string", Body="a string")
    assert s3.get_object(Bucket="test", Key="string")["Body"].read() == b"a string"

    s3.put_object(Bucket="test", Key="bytes", Body=b"some bytes")
    assert s3.get_object(Bucket="test", Key="bytes")["Body"].read() == b"some bytes"

    path = tmp_path / "foo.txt"
    path.write_text("a seekable file-like object")
    with open(path, "rb") as f:
        s3.put_object(Bucket="test", Key="seekable file-like object", Body=f)
    assert (
        s3.get_object(Bucket="test", Key="seekable file-like object")["Body"].read()
        == b"a seekable file-like object"
    )
