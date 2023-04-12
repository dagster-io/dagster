from dagster import ConfigurableResource


class IntVersionResource(ConfigurableResource):
    required_resource_keys: int


resource = IntVersionResource(required_resource_keys=3)
print(resource.required_resource_keys)
