from dagster._core.remote_representation.origin import (
    RegisteredCodeLocationOrigin,
    RemoteJobOrigin,
    RemoteRepositoryOrigin,
)

from dagster_aws.ecs.utils import get_task_definition_family, sanitize_family, sanitize_tag


def test_sanitize_family():
    assert sanitize_family("abc") == "abc"
    assert sanitize_family("abc123") == "abc123"
    assert sanitize_family("abc-123") == "abc-123"
    assert sanitize_family("abc_123") == "abc_123"
    assert sanitize_family("abc 123") == "abc123"
    assert sanitize_family("abc~123") == "abc123"


def test_sanitize_tag():
    assert sanitize_tag("abc") == "abc"
    assert sanitize_tag("abc123") == "abc123"
    assert sanitize_tag("foo.bar[filename_0]") == "foo-bar-filename_0"
    assert sanitize_tag("AaBbCc") == "AaBbCc"
    assert sanitize_tag("A" * 270) == "A" * 255


def test_get_task_definition_family():
    remote_job_origin = RemoteJobOrigin(
        repository_origin=RemoteRepositoryOrigin(
            repository_name="the_repo",
            code_location_origin=RegisteredCodeLocationOrigin(location_name="the_location"),
        ),
        job_name="the_job",
    )

    assert (
        get_task_definition_family("foo", remote_job_origin)
        == "foo_the_location_66c360f2_the_repo_b9c5532e_the_job_38cc9a96"
    )


def test_long_names():
    long_job_name = "a" * 512
    long_repo_name = "b" * 512
    long_location_name = "c" * 512

    remote_job_origin = RemoteJobOrigin(
        repository_origin=RemoteRepositoryOrigin(
            repository_name=long_repo_name,
            code_location_origin=RegisteredCodeLocationOrigin(location_name=long_location_name),
        ),
        job_name=long_job_name,
    )

    assert (
        get_task_definition_family("foo", remote_job_origin)
        == f"foo_{'c'*55}_d9023790_{'b'*55}_3956139d_{'a'*55}_164557fa"
    )
