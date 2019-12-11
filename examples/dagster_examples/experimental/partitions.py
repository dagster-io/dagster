import os
from datetime import date, timedelta

from dagster import (
    DagsterInvalidDefinitionError,
    Partition,
    PartitionSetDefinition,
    check,
    repository_partitions,
)


def date_partition_range(start, end=None):
    check.inst_param(start, 'start', date)
    check.opt_inst_param(end, 'end', date)
    if end and start > end:
        raise DagsterInvalidDefinitionError(
            'Selected date range start "{start}" is after date range end "{end}'.format(
                start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d')
            )
        )

    def get_date_range_partitions():
        current = start
        _end = end or date.today()
        date_names = []
        while current < _end:
            date_names.append(Partition(value=current, name=current.strftime('%Y-%m-%d')))
            current = current + timedelta(days=1)
        return date_names

    return get_date_range_partitions


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


ten_days_ago = date.today() - timedelta(days=10)
log_date_set = PartitionSetDefinition(
    name='date_partitions',
    pipeline_name='log_partitions',
    partition_fn=date_partition_range(ten_days_ago),
    environment_dict_fn_for_partition=partition_config_fn,
)


def dash_stats_datetime_partition_config(partition):
    current_date = partition.value
    yesterday = current_date - timedelta(days=1)
    date_string = yesterday.strftime("%Y-%m-%d")

    return {
        'resources': {'bigquery': None, 'slack': {'config': {'token': os.getenv('SLACK_TOKEN')}},},
        'solids': {'bq_solid': {'config': {'date': date_string}}},
    }


dash_stat_date_set = PartitionSetDefinition(
    name="dash_stat_date_partitions",
    pipeline_name='dash_stats',
    partition_fn=date_partition_range(ten_days_ago),
    environment_dict_fn_for_partition=lambda partition: {
        'resources': {'bigquery': None, 'slack': {'config': {'token': os.getenv('SLACK_TOKEN')}},},
        'solids': {'bq_solid': {'config': {'date': partition.value.strftime("%Y-%m-%d")}}},
    },
)

us_states_set = PartitionSetDefinition(
    name='state_partitions',
    pipeline_name='log_partitions',
    partition_fn=us_states,
    environment_dict_fn_for_partition=partition_config_fn,
)


@repository_partitions
def define_repository_partitions():
    return [dash_stat_date_set, log_date_set, us_states_set]
