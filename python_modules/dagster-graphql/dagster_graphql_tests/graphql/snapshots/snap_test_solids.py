# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_query_all_solids 1'] = {
    'repositoryOrError': {
        'usedSolids': [
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'add_four'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'composites_job'
                        },
                        'solidHandle': {
                            'handleID': 'add_four'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'add_one'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'composites_job'
                        },
                        'solidHandle': {
                            'handleID': 'add_four.adder_1.adder_1'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'composites_job'
                        },
                        'solidHandle': {
                            'handleID': 'add_four.adder_1.adder_2'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'composites_job'
                        },
                        'solidHandle': {
                            'handleID': 'add_four.adder_2.adder_1'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'composites_job'
                        },
                        'solidHandle': {
                            'handleID': 'add_four.adder_2.adder_2'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'add_two'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'composites_job'
                        },
                        'solidHandle': {
                            'handleID': 'add_four.adder_1'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'composites_job'
                        },
                        'solidHandle': {
                            'handleID': 'add_four.adder_2'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'adder'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'nested_job'
                        },
                        'solidHandle': {
                            'handleID': 'subgraph.adder'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'after_failure'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'chained_failure_job'
                        },
                        'solidHandle': {
                            'handleID': 'after_failure'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'always_succeed'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'chained_failure_job'
                        },
                        'solidHandle': {
                            'handleID': 'always_succeed'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'asset_1'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'failure_assets_job'
                        },
                        'solidHandle': {
                            'handleID': 'asset_1'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'asset_2'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'failure_assets_job'
                        },
                        'solidHandle': {
                            'handleID': 'asset_2'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'asset_3'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'failure_assets_job'
                        },
                        'solidHandle': {
                            'handleID': 'asset_3'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'asset_one'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'two_assets_job'
                        },
                        'solidHandle': {
                            'handleID': 'asset_one'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'asset_two'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'two_assets_job'
                        },
                        'solidHandle': {
                            'handleID': 'asset_two'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'asset_yields_observation'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'observation_job'
                        },
                        'solidHandle': {
                            'handleID': 'asset_yields_observation'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'bar'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'foo_job'
                        },
                        'solidHandle': {
                            'handleID': 'bar'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'baz'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'foo_job'
                        },
                        'solidHandle': {
                            'handleID': 'baz'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'can_fail'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_multi_output_job'
                        },
                        'solidHandle': {
                            'handleID': 'can_fail'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'collect'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'eventually_successful'
                        },
                        'solidHandle': {
                            'handleID': 'collect'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'conditionally_fail'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'chained_failure_job'
                        },
                        'solidHandle': {
                            'handleID': 'conditionally_fail'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'df_expectations_op'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'csv_hello_world_with_expectations'
                        },
                        'solidHandle': {
                            'handleID': 'df_expectations_op'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'div_four'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'composites_job'
                        },
                        'solidHandle': {
                            'handleID': 'div_four'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'div_two'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'composites_job'
                        },
                        'solidHandle': {
                            'handleID': 'div_four.div_1'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'composites_job'
                        },
                        'solidHandle': {
                            'handleID': 'div_four.div_2'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'downstream_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'hanging_graph_asset_job'
                        },
                        'solidHandle': {
                            'handleID': 'downstream_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'downstream_dynamic_partitioned_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'dynamic_partitioned_assets_job'
                        },
                        'solidHandle': {
                            'handleID': 'downstream_dynamic_partitioned_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'downstream_static_partitioned_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'static_partitioned_assets_job'
                        },
                        'solidHandle': {
                            'handleID': 'downstream_static_partitioned_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'downstream_time_partitioned_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'time_partitioned_assets_job'
                        },
                        'solidHandle': {
                            'handleID': 'downstream_time_partitioned_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'downstream_weekly_partitioned_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_4'
                        },
                        'solidHandle': {
                            'handleID': 'downstream_weekly_partitioned_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'dynamic_in_multipartitions_fail'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_2'
                        },
                        'solidHandle': {
                            'handleID': 'dynamic_in_multipartitions_fail'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'dynamic_in_multipartitions_success_job'
                        },
                        'solidHandle': {
                            'handleID': 'dynamic_in_multipartitions_fail'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'dynamic_in_multipartitions_success'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_2'
                        },
                        'solidHandle': {
                            'handleID': 'dynamic_in_multipartitions_success'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'dynamic_in_multipartitions_success_job'
                        },
                        'solidHandle': {
                            'handleID': 'dynamic_in_multipartitions_success'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'emit'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'dynamic_job'
                        },
                        'solidHandle': {
                            'handleID': 'emit'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'emit_failed_expectation'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'job_with_expectations'
                        },
                        'solidHandle': {
                            'handleID': 'emit_failed_expectation'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'emit_successful_expectation'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'job_with_expectations'
                        },
                        'solidHandle': {
                            'handleID': 'emit_successful_expectation'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'emit_successful_expectation_no_metadata'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'job_with_expectations'
                        },
                        'solidHandle': {
                            'handleID': 'emit_successful_expectation_no_metadata'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'emit_ten'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'dynamic_job'
                        },
                        'solidHandle': {
                            'handleID': 'emit_ten'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'fail'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'eventually_successful'
                        },
                        'solidHandle': {
                            'handleID': 'fail'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'eventually_successful'
                        },
                        'solidHandle': {
                            'handleID': 'fail_2'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'eventually_successful'
                        },
                        'solidHandle': {
                            'handleID': 'fail_3'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'fail_partition_materialization'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'fail_partition_materialization_job'
                        },
                        'solidHandle': {
                            'handleID': 'fail_partition_materialization'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'fail_subset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'job_with_invalid_definition_error'
                        },
                        'solidHandle': {
                            'handleID': 'fail_subset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'first_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'hanging_job'
                        },
                        'solidHandle': {
                            'handleID': 'first_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'foo'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'foo_job'
                        },
                        'solidHandle': {
                            'handleID': 'foo'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'foo_bar'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'foo_job'
                        },
                        'solidHandle': {
                            'handleID': 'foo_bar'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'fresh_diamond_bottom'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_0'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_bottom'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_1'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_bottom'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_2'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_bottom'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_3'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_bottom'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_4'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_bottom'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'fresh_diamond_assets'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_bottom'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'fresh_diamond_left'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_0'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_left'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_1'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_left'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_2'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_left'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_3'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_left'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_4'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_left'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'fresh_diamond_assets'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_left'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'fresh_diamond_right'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_0'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_right'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_1'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_right'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_2'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_right'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_3'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_right'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_4'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_right'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'fresh_diamond_assets'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_right'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'fresh_diamond_top'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_0'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_top'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_1'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_top'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_2'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_top'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_3'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_top'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_4'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_top'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'fresh_diamond_assets'
                        },
                        'solidHandle': {
                            'handleID': 'fresh_diamond_top'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'get_input_one'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_multi_input_early_terminate_job'
                        },
                        'solidHandle': {
                            'handleID': 'get_input_one'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'get_input_two'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_multi_input_early_terminate_job'
                        },
                        'solidHandle': {
                            'handleID': 'get_input_two'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'grouped_asset_1'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'named_groups_job'
                        },
                        'solidHandle': {
                            'handleID': 'grouped_asset_1'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'grouped_asset_2'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'named_groups_job'
                        },
                        'solidHandle': {
                            'handleID': 'grouped_asset_2'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'grouped_asset_4'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'named_groups_job'
                        },
                        'solidHandle': {
                            'handleID': 'grouped_asset_4'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'hanging_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'hanging_job'
                        },
                        'solidHandle': {
                            'handleID': 'hanging_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'hanging_graph'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'hanging_graph_asset_job'
                        },
                        'solidHandle': {
                            'handleID': 'hanging_graph'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'hanging_op'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'hanging_graph_asset_job'
                        },
                        'solidHandle': {
                            'handleID': 'hanging_graph.hanging_op'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'hanging_partition_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'hanging_partition_asset_job'
                        },
                        'solidHandle': {
                            'handleID': 'hanging_partition_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'hard_fail_or_0'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'hard_failer'
                        },
                        'solidHandle': {
                            'handleID': 'hard_fail_or_0'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'increment'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'hard_failer'
                        },
                        'solidHandle': {
                            'handleID': 'increment'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'loop'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'infinite_loop_job'
                        },
                        'solidHandle': {
                            'handleID': 'loop'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'materialize'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'materialization_job'
                        },
                        'solidHandle': {
                            'handleID': 'materialize'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'middle_static_partitioned_asset_1'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'static_partitioned_assets_job'
                        },
                        'solidHandle': {
                            'handleID': 'middle_static_partitioned_asset_1'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'middle_static_partitioned_asset_2'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'static_partitioned_assets_job'
                        },
                        'solidHandle': {
                            'handleID': 'middle_static_partitioned_asset_2'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'multi'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_multi_output_job'
                        },
                        'solidHandle': {
                            'handleID': 'multi'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'multipartitions_1'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_1'
                        },
                        'solidHandle': {
                            'handleID': 'multipartitions_1'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'multipartitions_job'
                        },
                        'solidHandle': {
                            'handleID': 'multipartitions_1'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'multipartitions_2'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_1'
                        },
                        'solidHandle': {
                            'handleID': 'multipartitions_2'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'multipartitions_job'
                        },
                        'solidHandle': {
                            'handleID': 'multipartitions_2'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'multipartitions_fail'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_1'
                        },
                        'solidHandle': {
                            'handleID': 'multipartitions_fail'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'multipartitions_fail_job'
                        },
                        'solidHandle': {
                            'handleID': 'multipartitions_fail'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'multiply_by_two'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'dynamic_job'
                        },
                        'solidHandle': {
                            'handleID': 'double_total'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'dynamic_job'
                        },
                        'solidHandle': {
                            'handleID': 'multiply_by_two'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'multiply_inputs'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'dynamic_job'
                        },
                        'solidHandle': {
                            'handleID': 'multiply_inputs'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'my_op'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'hanging_graph_asset_job'
                        },
                        'solidHandle': {
                            'handleID': 'hanging_graph.my_op'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'daily_partitioned_job'
                        },
                        'solidHandle': {
                            'handleID': 'my_op'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'memoization_job'
                        },
                        'solidHandle': {
                            'handleID': 'my_op'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'static_partitioned_job'
                        },
                        'solidHandle': {
                            'handleID': 'my_op'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'never_runs_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'hanging_job'
                        },
                        'solidHandle': {
                            'handleID': 'never_runs_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'never_runs_op'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'hanging_graph_asset_job'
                        },
                        'solidHandle': {
                            'handleID': 'hanging_graph.never_runs_op'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'no_multipartitions_1'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_0'
                        },
                        'solidHandle': {
                            'handleID': 'no_multipartitions_1'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'no_multipartitions_job'
                        },
                        'solidHandle': {
                            'handleID': 'no_multipartitions_1'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'no_output'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_multi_output_job'
                        },
                        'solidHandle': {
                            'handleID': 'child_multi_skip'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'retry_multi_output_job'
                        },
                        'solidHandle': {
                            'handleID': 'child_skip'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'retry_multi_output_job'
                        },
                        'solidHandle': {
                            'handleID': 'grandchild_fail'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'noop_op'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'config_with_map'
                        },
                        'solidHandle': {
                            'handleID': 'noop_op'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'more_complicated_config'
                        },
                        'solidHandle': {
                            'handleID': 'noop_op'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'noop_job'
                        },
                        'solidHandle': {
                            'handleID': 'noop_op'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'simple_job_a'
                        },
                        'solidHandle': {
                            'handleID': 'noop_op'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'simple_job_b'
                        },
                        'solidHandle': {
                            'handleID': 'noop_op'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'composed_graph'
                        },
                        'solidHandle': {
                            'handleID': 'simple_graph.noop_op'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'one'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'job_with_invalid_definition_error'
                        },
                        'solidHandle': {
                            'handleID': 'one'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'op_1'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'two_ins_job'
                        },
                        'solidHandle': {
                            'handleID': 'op_1'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'nested_job'
                        },
                        'solidHandle': {
                            'handleID': 'subgraph.op_1'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'op_2'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'two_ins_job'
                        },
                        'solidHandle': {
                            'handleID': 'op_2'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'nested_job'
                        },
                        'solidHandle': {
                            'handleID': 'subgraph.op_2'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'op_asset_a'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'multi_asset_job'
                        },
                        'solidHandle': {
                            'handleID': 'op_asset_a'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'single_asset_job'
                        },
                        'solidHandle': {
                            'handleID': 'op_asset_a'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'op_asset_b'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'multi_asset_job'
                        },
                        'solidHandle': {
                            'handleID': 'op_asset_b'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'op_partitioned_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'partitioned_asset_job'
                        },
                        'solidHandle': {
                            'handleID': 'op_partitioned_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'op_that_gets_tags'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'hello_world_with_tags'
                        },
                        'solidHandle': {
                            'handleID': 'op_that_gets_tags'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'op_with_2_ins'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'two_ins_job'
                        },
                        'solidHandle': {
                            'handleID': 'op_with_2_ins'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'op_with_config'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'job_with_default_config'
                        },
                        'solidHandle': {
                            'handleID': 'op_with_config'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'op_with_input_output_metadata'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'job_with_input_output_metadata'
                        },
                        'solidHandle': {
                            'handleID': 'op_with_input_output_metadata'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'op_with_list'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'job_with_list'
                        },
                        'solidHandle': {
                            'handleID': 'op_with_list'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'op_with_map_config'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'config_with_map'
                        },
                        'solidHandle': {
                            'handleID': 'op_with_map_config'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'op_with_multilayered_config'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'more_complicated_nested_config'
                        },
                        'solidHandle': {
                            'handleID': 'op_with_multilayered_config'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'op_with_required_resource'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'required_resource_config_job'
                        },
                        'solidHandle': {
                            'handleID': 'op_with_required_resource'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'required_resource_job'
                        },
                        'solidHandle': {
                            'handleID': 'op_with_required_resource'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'op_with_three_field_config'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'more_complicated_config'
                        },
                        'solidHandle': {
                            'handleID': 'op_with_three_field_config'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'passthrough'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_multi_output_job'
                        },
                        'solidHandle': {
                            'handleID': 'child_fail'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'plus_one'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'nested_job'
                        },
                        'solidHandle': {
                            'handleID': 'plus_one'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'nested_job'
                        },
                        'solidHandle': {
                            'handleID': 'subgraph.plus_one'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'reset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'eventually_successful'
                        },
                        'solidHandle': {
                            'handleID': 'reset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'return_any'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'scalar_output_job'
                        },
                        'solidHandle': {
                            'handleID': 'return_any'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'return_bool'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'scalar_output_job'
                        },
                        'solidHandle': {
                            'handleID': 'return_bool'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'return_foo'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'no_config_chain_job'
                        },
                        'solidHandle': {
                            'handleID': 'return_foo'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'return_hello'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'no_config_job'
                        },
                        'solidHandle': {
                            'handleID': 'return_hello'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'return_hello_world'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'no_config_chain_job'
                        },
                        'solidHandle': {
                            'handleID': 'return_hello_world'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'return_int'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'scalar_output_job'
                        },
                        'solidHandle': {
                            'handleID': 'return_int'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'return_integer'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'integers'
                        },
                        'solidHandle': {
                            'handleID': 'return_integer'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'return_one'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_multi_input_early_terminate_job'
                        },
                        'solidHandle': {
                            'handleID': 'return_one'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'return_six'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'loggers_job'
                        },
                        'solidHandle': {
                            'handleID': 'return_six'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'return_str'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'scalar_output_job'
                        },
                        'solidHandle': {
                            'handleID': 'return_str'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'simple_graph'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'composed_graph'
                        },
                        'solidHandle': {
                            'handleID': 'simple_graph'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'simple_op'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'tagged_job'
                        },
                        'solidHandle': {
                            'handleID': 'simple_op'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'spawn'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'eventually_successful'
                        },
                        'solidHandle': {
                            'handleID': 'spawn'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'spew'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'spew_job'
                        },
                        'solidHandle': {
                            'handleID': 'spew'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'start'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_resource_job'
                        },
                        'solidHandle': {
                            'handleID': 'start'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'subgraph'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'nested_job'
                        },
                        'solidHandle': {
                            'handleID': 'subgraph'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'sum_inputs'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_multi_input_early_terminate_job'
                        },
                        'solidHandle': {
                            'handleID': 'sum_inputs'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'sum_numbers'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'dynamic_job'
                        },
                        'solidHandle': {
                            'handleID': 'sum_numbers'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'sum_op'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'csv_hello_world'
                        },
                        'solidHandle': {
                            'handleID': 'sum_op'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'csv_hello_world_df_input'
                        },
                        'solidHandle': {
                            'handleID': 'sum_op'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'csv_hello_world_two'
                        },
                        'solidHandle': {
                            'handleID': 'sum_op'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'csv_hello_world_with_expectations'
                        },
                        'solidHandle': {
                            'handleID': 'sum_op'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'sum_sq_op'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'csv_hello_world'
                        },
                        'solidHandle': {
                            'handleID': 'sum_sq_op'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'csv_hello_world_df_input'
                        },
                        'solidHandle': {
                            'handleID': 'sum_sq_op'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'csv_hello_world_with_expectations'
                        },
                        'solidHandle': {
                            'handleID': 'sum_sq_op'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'tag_asset_op'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'asset_tag_job'
                        },
                        'solidHandle': {
                            'handleID': 'tag_asset_op'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'takes_an_enum'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'job_with_enum_config'
                        },
                        'solidHandle': {
                            'handleID': 'takes_an_enum'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'the_op'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'req_config_job'
                        },
                        'solidHandle': {
                            'handleID': 'the_op'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'throw_a_thing'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'naughty_programmer_job'
                        },
                        'solidHandle': {
                            'handleID': 'throw_a_thing'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'typed_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_0'
                        },
                        'solidHandle': {
                            'handleID': 'typed_asset'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_1'
                        },
                        'solidHandle': {
                            'handleID': 'typed_asset'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_2'
                        },
                        'solidHandle': {
                            'handleID': 'typed_asset'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_3'
                        },
                        'solidHandle': {
                            'handleID': 'typed_asset'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_4'
                        },
                        'solidHandle': {
                            'handleID': 'typed_asset'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'typed_assets'
                        },
                        'solidHandle': {
                            'handleID': 'typed_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'typed_multi_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_0'
                        },
                        'solidHandle': {
                            'handleID': 'typed_multi_asset'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_1'
                        },
                        'solidHandle': {
                            'handleID': 'typed_multi_asset'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_2'
                        },
                        'solidHandle': {
                            'handleID': 'typed_multi_asset'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_3'
                        },
                        'solidHandle': {
                            'handleID': 'typed_multi_asset'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_4'
                        },
                        'solidHandle': {
                            'handleID': 'typed_multi_asset'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'typed_assets'
                        },
                        'solidHandle': {
                            'handleID': 'typed_multi_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'unconnected'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'foo_job'
                        },
                        'solidHandle': {
                            'handleID': 'unconnected'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'ungrouped_asset_3'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'named_groups_job'
                        },
                        'solidHandle': {
                            'handleID': 'ungrouped_asset_3'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'ungrouped_asset_5'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'named_groups_job'
                        },
                        'solidHandle': {
                            'handleID': 'ungrouped_asset_5'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'unpartitioned_upstream_of_partitioned'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_0'
                        },
                        'solidHandle': {
                            'handleID': 'unpartitioned_upstream_of_partitioned'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_1'
                        },
                        'solidHandle': {
                            'handleID': 'unpartitioned_upstream_of_partitioned'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_2'
                        },
                        'solidHandle': {
                            'handleID': 'unpartitioned_upstream_of_partitioned'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_3'
                        },
                        'solidHandle': {
                            'handleID': 'unpartitioned_upstream_of_partitioned'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_4'
                        },
                        'solidHandle': {
                            'handleID': 'unpartitioned_upstream_of_partitioned'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'untyped_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_0'
                        },
                        'solidHandle': {
                            'handleID': 'untyped_asset'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_1'
                        },
                        'solidHandle': {
                            'handleID': 'untyped_asset'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_2'
                        },
                        'solidHandle': {
                            'handleID': 'untyped_asset'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_3'
                        },
                        'solidHandle': {
                            'handleID': 'untyped_asset'
                        }
                    },
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_4'
                        },
                        'solidHandle': {
                            'handleID': 'untyped_asset'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'typed_assets'
                        },
                        'solidHandle': {
                            'handleID': 'untyped_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'upstream_daily_partitioned_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': '__ASSET_JOB_3'
                        },
                        'solidHandle': {
                            'handleID': 'upstream_daily_partitioned_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'upstream_dynamic_partitioned_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'dynamic_partitioned_assets_job'
                        },
                        'solidHandle': {
                            'handleID': 'upstream_dynamic_partitioned_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'upstream_static_partitioned_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'static_partitioned_assets_job'
                        },
                        'solidHandle': {
                            'handleID': 'upstream_static_partitioned_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'upstream_time_partitioned_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'time_partitioned_assets_job'
                        },
                        'solidHandle': {
                            'handleID': 'upstream_time_partitioned_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'will_fail'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_resource_job'
                        },
                        'solidHandle': {
                            'handleID': 'will_fail'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'yield_partition_materialization'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'partition_materialization_job'
                        },
                        'solidHandle': {
                            'handleID': 'yield_partition_materialization'
                        }
                    }
                ]
            }
        ]
    }
}
