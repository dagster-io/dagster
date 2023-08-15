from dagster import ConfigurableResource


class DataGeneratorResource(ConfigurableResource):
    num_days: int = 4

    def get_signups(self):
        return [1, 2, 3, 4, 5]
