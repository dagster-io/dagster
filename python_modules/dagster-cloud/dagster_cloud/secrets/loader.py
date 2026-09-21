from typing import Any

from dagster._core.secrets import SecretsLoader
from dagster._serdes import ConfigurableClass
from dagster._serdes.config_class import ConfigurableClassData
from typing_extensions import Self

SECRETS_QUERY = """
query Secrets($locationName: String) {
    scopedSecrets(locationName: $locationName) {
        secretName
        secretValue
        locationNames
    }
}
"""


class DagsterCloudSecretsLoader(SecretsLoader, ConfigurableClass):
    def __init__(
        self,
        inst_data=None,
    ):
        self._inst_data = inst_data

    def _execute_query(self, query, variables=None):
        return self._instance.graphql_client.execute(query, variable_values=variables)  # ty: ignore[unresolved-attribute]

    def get_secrets_for_environment(self, location_name: str | None) -> dict[str, str]:
        res = self._execute_query(
            SECRETS_QUERY,
            variables={"locationName": location_name},
        )

        secrets = res["data"]["scopedSecrets"]

        # Place secrets scoped to this location at the end so that they take priority over secrets
        # with the same name but no location scopes
        secrets = sorted(secrets, key=lambda secret: "1" if secret["locationNames"] else "0")

        return {secret["secretName"]: secret["secretValue"] for secret in secrets}

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @classmethod
    def from_config_value(cls, inst_data: ConfigurableClassData, config_value: Any) -> Self:
        return cls(inst_data=inst_data, **config_value)
