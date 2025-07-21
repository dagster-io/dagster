from dagster import AllPartitionMapping, AssetIn, asset


def test_partition_mapping_not_filtered_due_to_len_zero():
    @asset(ins={"upstream": AssetIn(partition_mapping=AllPartitionMapping())})
    def downstream(upstream):
        return upstream

    # Confirm that the input wasn't filtered out due to falsey partition_mapping
    assert "upstream" in downstream.node_keys_by_input_name
