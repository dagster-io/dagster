from dagster import AssetKey, AssetsDefinition, In, Nothing, asset, define_asset_job, op, repository
from dagster._core.definitions.assets_lazy import AssetsDefinitionMetadata, LazyAssetsDefinition
from dagster._core.test_utils import instance_for_test
from dagster._serdes.utils import hash_str


class SomeLazyAsset(LazyAssetsDefinition):
    def __init__(self, connection_id: str, config: str):
        self.connection_id = connection_id
        self.config = config
        self.generated_metadata = 0
        super().__init__(self, unique_id=hash_str(f"{connection_id}{config}"))

    def generate_metadata(self) -> AssetsDefinitionMetadata:
        self.generated_metadata += 1  # for testing

        # pretend this is an external API
        input_keys_for_connection_id = {
            "conn1": {AssetKey("sA")},
            "conn2": {AssetKey("sB"), AssetKey("sC")},
        }
        output_keys_for_connection_id = {"conn1": {AssetKey("dA")}, "conn2": {AssetKey("dB")}}

        return AssetsDefinitionMetadata(
            input_keys=input_keys_for_connection_id[self.connection_id],
            output_keys=output_keys_for_connection_id[self.connection_id],
        )

    def generate_assets(self, metadata: AssetsDefinitionMetadata):
        keys_by_input_name = {"_".join(ak.path): ak for ak in metadata.input_keys}

        @op(name=self._unique_id, ins={name: In(Nothing) for name in keys_by_input_name.keys()})
        def _op():
            return 1

        return [
            AssetsDefinition.from_op(
                _op,
                keys_by_input_name=keys_by_input_name,
                keys_by_output_name={"result": list(metadata.output_keys)[0]},
            )
        ]


def test_lazy_uses_cache():
    @asset
    def regular_asset(dA, dB):
        return dA + dB

    lazy_asset1 = SomeLazyAsset(connection_id="conn1", config="blah")
    lazy_asset2 = SomeLazyAsset(connection_id="conn2", config="blahblah")

    def get_repo():
        @repository
        def my_repo():
            return [
                lazy_asset1,
                lazy_asset2,
                regular_asset,
                define_asset_job("all_assets", selection="*"),
            ]

        return my_repo

    with instance_for_test() as instance:

        get_repo().get_job("all_assets").execute_in_process(instance=instance)

        assert lazy_asset1.generated_metadata == 1
        assert lazy_asset2.generated_metadata == 1

        get_repo().get_job("all_assets").execute_in_process(instance=instance)

        # on second run, can used cached info stored on instance
        assert lazy_asset1.generated_metadata == 1
        assert lazy_asset2.generated_metadata == 1

    with instance_for_test() as instance:
        # now that we have a new instance, no cached data stored
        get_repo().get_job("all_assets").execute_in_process(instance=instance)

        assert lazy_asset1.generated_metadata == 2
        assert lazy_asset2.generated_metadata == 2

        get_repo().get_job("all_assets").execute_in_process(instance=instance)

        assert lazy_asset1.generated_metadata == 2
        assert lazy_asset2.generated_metadata == 2
