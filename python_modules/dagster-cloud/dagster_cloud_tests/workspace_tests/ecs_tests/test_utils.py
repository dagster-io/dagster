import pytest
from dagster._core.remote_origin import (
    RegisteredCodeLocationOrigin,
    RemoteJobOrigin,
    RemoteRepositoryOrigin,
)
from dagster_cloud.workspace.ecs.utils import (
    get_run_task_definition_family,
    get_server_task_definition_family,
)


@pytest.fixture
def job_origin():
    return RemoteJobOrigin(
        repository_origin=RemoteRepositoryOrigin(
            repository_name="the_repo",
            code_location_origin=RegisteredCodeLocationOrigin(location_name="the_location"),
        ),
        job_name="the_job",
    )


@pytest.fixture
def long_job_origin():
    long_job_name = "a" * 512
    long_repo_name = "b" * 512
    long_location_name = "c" * 512

    return RemoteJobOrigin(
        repository_origin=RemoteRepositoryOrigin(
            repository_name=long_repo_name,
            code_location_origin=RegisteredCodeLocationOrigin(location_name=long_location_name),
        ),
        job_name=long_job_name,
    )


@pytest.fixture
def other_long_job_origin():
    long_job_name = "d" * 512
    long_repo_name = "e" * 512
    long_location_name = "f" * 512

    return RemoteJobOrigin(
        repository_origin=RemoteRepositoryOrigin(
            repository_name=long_repo_name,
            code_location_origin=RegisteredCodeLocationOrigin(location_name=long_location_name),
        ),
        job_name=long_job_name,
    )


def test_task_definition_family_long_location(long_job_origin, other_long_job_origin):
    family = get_run_task_definition_family("foo", "hooli", "prod", long_job_origin)

    assert (
        family
        == "foo_hooli_prod_ccccccccccccccccccccccc_d9023790_bbbbbbbbbbbbbbbbbbbbbbb_3956139d_aaaaaaaaaaaaaaaaaaaaaaa_164557fa"
    )

    assert family != get_run_task_definition_family("foo", "hooli", "prod", other_long_job_origin)


def test_org_deployment_scope(job_origin):
    assert (
        get_run_task_definition_family("foo", "hooli", "prod", job_origin)
        == "foo_hooli_prod_the_location_66c360f2_the_repo_b9c5532e_the_job_38cc9a96"
    )

    # different deployment = new family
    assert get_run_task_definition_family(
        "foo", "hooli", "prod", job_origin
    ) != get_run_task_definition_family("foo", "hooli", "dev", job_origin)

    # different org = new family
    assert get_run_task_definition_family(
        "foo", "hooli", "prod", job_origin
    ) != get_run_task_definition_family("foo", "acme", "prod", job_origin)

    # different prefix = new family

    assert get_run_task_definition_family(
        "foo", "hooli", "prod", job_origin
    ) != get_run_task_definition_family("bar", "hooli", "prod", job_origin)

    # same everything = same
    assert get_run_task_definition_family(
        "foo", "hooli", "prod", job_origin
    ) == get_run_task_definition_family("foo", "hooli", "prod", job_origin)


def test_server_task_definition_family_long_location():
    long_location_name = "abcd" * 255
    different_long_location_name = "abcd" * 512

    assert get_server_task_definition_family(
        "foo", "hooli", "prod", long_location_name
    ) != get_server_task_definition_family("foo", "hooli", "prod", different_long_location_name)


def test_server_task_definition_family_short_location():
    short_location_name = "abcd"
    other_short_location_name = "efgh"

    assert get_server_task_definition_family(
        "foo", "hooli", "prod", short_location_name
    ) != get_server_task_definition_family("foo", "hooli", "prod", other_short_location_name)


def test_server_org_deployment_scope():
    location_name = "abcd"

    # different deployment = new family
    assert get_server_task_definition_family(
        "foo", "hooli", "prod", location_name
    ) != get_server_task_definition_family("foo", "hooli", "dev", location_name)

    # different org = new family
    assert get_server_task_definition_family(
        "foo", "hooli", "prod", location_name
    ) != get_server_task_definition_family("foo", "acme", "prod", location_name)

    # same everything = same
    assert get_server_task_definition_family(
        "foo", "hooli", "prod", location_name
    ) == get_server_task_definition_family("foo", "hooli", "prod", location_name)
