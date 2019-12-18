from dagster import PartitionSetDefinition, repository_partitions


# fmt: off
def us_states():
    return [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "ID", "IL", "IN",
        "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH",
        "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT",
        "VT", "VA", "WA", "WV", "WI", "WY",
    ]
# fmt: on


def partition_config_fn(partition):
    return {
        'solids': {
            'announce_partition': {'config': {'partition': "Partition is: " + str(partition.value)}}
        }
    }


us_states_set = PartitionSetDefinition(
    name='state_partitions',
    pipeline_name='log_partitions',
    partition_fn=us_states,
    environment_dict_fn_for_partition=partition_config_fn,
)


@repository_partitions
def define_repository_partitions():
    return [us_states_set]
