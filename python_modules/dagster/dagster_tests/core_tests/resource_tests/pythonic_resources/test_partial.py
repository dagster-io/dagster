import pytest
from dagster import (
    asset,
)
from dagster._config.pythonic_config import (
    ConfigurableResource,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.errors import (
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
)


def test_structured_resource_partial_config_empty() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str
        postfix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}{self.postfix}")

    @asset
    def hello_world_asset(writer: WriterResource):
        writer.output("hello, world!")

    # No params set with partial
    defs = Definitions(
        assets=[hello_world_asset],
        resources={"writer": WriterResource.partial()},
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process({"resources": {"writer": {"config": {"prefix": ">", "postfix": "<"}}}})
        .success
    )
    assert out_txt == [">hello, world!<"]


def test_structured_resource_partial_config_basic() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str
        postfix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}{self.postfix}")

    @asset
    def hello_world_asset(writer: WriterResource):
        writer.output("hello, world!")

    # One param set as partial
    defs = Definitions(
        assets=[hello_world_asset],
        resources={"writer": WriterResource.partial(prefix="(")},
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process({"resources": {"writer": {"config": {"postfix": ")"}}}})
        .success
    )
    assert out_txt == ["(hello, world!)"]
    out_txt.clear()

    # Two params set as partial
    defs = Definitions(
        assets=[hello_world_asset],
        resources={"writer": WriterResource.partial(prefix="{", postfix="}")},
    )

    assert defs.get_implicit_global_asset_job_def().execute_in_process().success
    assert out_txt == ["{hello, world!}"]


def test_structured_resource_partial_config_overriding() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str
        postfix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}{self.postfix}")

    @asset
    def hello_world_asset(writer: WriterResource):
        writer.output("hello, world!")

    # Overriding partial param
    defs = Definitions(
        assets=[hello_world_asset],
        resources={"writer": WriterResource.partial(prefix="{")},
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process({"resources": {"writer": {"config": {"prefix": "[", "postfix": "]"}}}})
        .success
    )
    assert out_txt == ["[hello, world!]"]
    out_txt.clear()

    # Overriding both partial params
    defs = Definitions(
        assets=[hello_world_asset],
        resources={"writer": WriterResource.partial(prefix="<", postfix=">")},
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process({"resources": {"writer": {"config": {"prefix": "*", "postfix": "*"}}}})
        .success
    )
    assert out_txt == ["*hello, world!*"]
    out_txt.clear()


def test_nested_resources_partial_config() -> None:
    class AWSCredentialsResource(ConfigurableResource):
        username: str
        password: str

    class S3Resource(ConfigurableResource):
        aws_credentials: AWSCredentialsResource
        bucket_name: str

    class EC2Resource(ConfigurableResource):
        aws_credentials: AWSCredentialsResource

    completed = {}

    @asset
    def my_asset(s3: S3Resource, ec2: EC2Resource):
        assert s3.aws_credentials.username == "foo"
        assert s3.aws_credentials.password == "bar"
        assert s3.bucket_name == "my_bucket"

        assert ec2.aws_credentials.username == "foo"
        assert ec2.aws_credentials.password == "bar"

        completed["yes"] = True

    aws_credentials = AWSCredentialsResource.partial(username="foo")
    defs = Definitions(
        assets=[my_asset],
        resources={
            "aws_credentials": aws_credentials,
            "s3": S3Resource(bucket_name="my_bucket", aws_credentials=aws_credentials),
            "ec2": EC2Resource(aws_credentials=aws_credentials),
        },
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(
            {
                "resources": {
                    "aws_credentials": {
                        "config": {
                            "password": "bar",
                        }
                    }
                }
            }
        )
        .success
    )
    assert completed["yes"]


def test_nested_resources_partial_config_complex() -> None:
    class CredentialsResource(ConfigurableResource):
        username: str
        password: str

    class DBConfigResource(ConfigurableResource):
        creds: CredentialsResource
        host: str
        database: str

    class DBResource(ConfigurableResource):
        config: DBConfigResource

    completed = {}

    @asset
    def my_asset(db: DBResource):
        assert db.config.creds.username == "foo"
        assert db.config.creds.password == "bar"
        assert db.config.host == "localhost"
        assert db.config.database == "my_db"
        completed["yes"] = True

    credentials = CredentialsResource.partial(username="foo")
    db_config = DBConfigResource.partial(creds=credentials, host="localhost")
    db = DBResource(config=db_config)

    defs = Definitions(
        assets=[my_asset],
        resources={
            "credentials": credentials,
            "db_config": db_config,
            "db": db,
        },
    )

    assert (
        defs.get_implicit_global_asset_job_def()
        .execute_in_process(
            {
                "resources": {
                    "credentials": {
                        "config": {
                            "password": "bar",
                        }
                    },
                    "db_config": {
                        "config": {
                            "host": "localhost",
                            "database": "my_db",
                        }
                    },
                }
            }
        )
        .success
    )
    assert completed["yes"]


def test_structured_configure_at_launch_error() -> None:
    # Cannot pass any configuration information into a resource when calling
    # configure_at_launch, you should instead call partial

    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str
        postfix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}{self.postfix}")

    @asset
    def hello_world_asset(writer: WriterResource):
        writer.output("hello, world!")

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "'WriterResource.configure_at_launch' was called but non-resource parameters were"
            " passed: \\['prefix'\\]. Did you mean to call 'WriterResource.partial' instead?"
        ),
    ):
        Definitions(
            assets=[hello_world_asset],
            resources={"writer": WriterResource.configure_at_launch(prefix="(")},
        )

    with pytest.raises(
        DagsterInvalidDefinitionError,
        match=(
            "'WriterResource.configure_at_launch' was called but non-resource parameters were"
            " passed: \\['prefix', 'postfix'\\]. Did you mean to call 'WriterResource.partial'"
            " instead?"
        ),
    ):
        Definitions(
            assets=[hello_world_asset],
            resources={"writer": WriterResource.configure_at_launch(prefix="(", postfix=")")},
        )


def test_structured_resource_partial_config_missing() -> None:
    out_txt = []

    class WriterResource(ConfigurableResource):
        prefix: str
        postfix: str

        def output(self, text: str) -> None:
            out_txt.append(f"{self.prefix}{text}{self.postfix}")

    @asset
    def hello_world_asset(writer: WriterResource):
        writer.output("hello, world!")

    # One param set as partial
    defs = Definitions(
        assets=[hello_world_asset],
        resources={"writer": WriterResource.partial(prefix="(")},
    )

    with pytest.raises(
        DagsterInvalidConfigError,
        match=(
            'Missing required config entry "resources" at the root. Sample config for missing'
            " entry: {'resources': {'writer': {'config': {'postfix': '...'}}}}"
        ),
    ):
        assert defs.get_implicit_global_asset_job_def().execute_in_process().success
