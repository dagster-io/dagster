class DagsterAirbyteTranslator:
    def get_group_name_from_connection(self):
        # Based on
        # connection_to_group_fn: Optional[Callable[[str], Optional[str]]] = (_clean_name,)
        raise NotImplementedError

    def get_group_name_from_connection_metadata(self):
        # Based on
        # connection_meta_to_group_fn: Optional[Callable[[AirbyteConnectionMetadata], Optional[str]]] = (
        #    None,
        # )
        raise NotImplementedError

    def get_asset_key(self):
        # Based on
        # connection_to_asset_key_fn: Optional[Callable[[AirbyteConnectionMetadata, str], AssetKey]] = (None,)
        raise NotImplementedError

    def get_auto_materialize_policy(self):
        # Based on
        # connection_to_auto_materialize_policy_fn: Optional[
        #    Callable[[AirbyteConnectionMetadata], Optional[AutoMaterializePolicy]]
        # ] = (None,)
        raise NotImplementedError

    def get_freshness_policy(self):
        # Based on
        # connection_to_freshness_policy_fn: Optional[
        #    Callable[[AirbyteConnectionMetadata], Optional[FreshnessPolicy]]
        # ] = (None,)
        raise NotImplementedError

    def get_io_manager_key(self):
        # Based on
        # connection_to_io_manager_key_fn: Optional[Callable[[str], Optional[str]]] = (None,)
        raise NotImplementedError
