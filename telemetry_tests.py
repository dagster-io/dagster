from dagster import ResourceDefinition, ConfigurableResource, IOManagerDefinition
from dagster._config.pythonic_config import ConfigurableResourceFactory

def test_telemetry():
    package_name = "dagster_snowflake"

    package = __import__(package_name)

    resources = dict([(name, cls) for name, cls in package.__dict__.items() if isinstance(cls, (ResourceDefinition, ConfigurableResource, IOManagerDefinition, ConfigurableResourceFactory)) or (isinstance(cls, type) and issubclass(cls, (ResourceDefinition, ConfigurableResource, IOManagerDefinition, ConfigurableResourceFactory)))])

    for _, klass in resources.items():
        assert klass._dagster_maintained # TODO helpful error message 
        print(klass)


    print("blah")