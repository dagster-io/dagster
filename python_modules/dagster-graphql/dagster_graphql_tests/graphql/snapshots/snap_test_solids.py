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
                    'name': 'a_solid_with_multilayered_config'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'more_complicated_nested_config'
                        },
                        'solidHandle': {
                            'handleID': 'a_solid_with_multilayered_config'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'a_solid_with_three_field_config'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'more_complicated_config'
                        },
                        'solidHandle': {
                            'handleID': 'a_solid_with_three_field_config'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'add_four'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'composites_pipeline'
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
                            'name': 'composites_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'add_four.adder_1.adder_1'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'composites_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'add_four.adder_1.adder_2'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'composites_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'add_four.adder_2.adder_1'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'composites_pipeline'
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
                            'name': 'composites_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'add_four.adder_1'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'composites_pipeline'
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
                    'name': 'after_failure'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'chained_failure_pipeline'
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
                    'name': 'alp_a'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'asset_lineage_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'alp_a'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'alp_b'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'asset_lineage_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'alp_b'
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
                            'name': 'chained_failure_pipeline'
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
                    'name': 'apply_to_three'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'multi_mode_with_resources'
                        },
                        'solidHandle': {
                            'handleID': 'apply_to_three'
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
                            'name': 'retry_multi_output_pipeline'
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
                    'name': 'conditionally_fail'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'chained_failure_pipeline'
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
                    'name': 'df_expectations_solid'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'csv_hello_world_with_expectations'
                        },
                        'solidHandle': {
                            'handleID': 'df_expectations_solid'
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
                            'name': 'composites_pipeline'
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
                            'name': 'composites_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'div_four.div_1'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'composites_pipeline'
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
                    'name': 'emit'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'dynamic_pipeline'
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
                            'name': 'pipeline_with_expectations'
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
                            'name': 'pipeline_with_expectations'
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
                            'name': 'pipeline_with_expectations'
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
                            'name': 'dynamic_pipeline'
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
                    'name': 'fail_subset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'pipeline_with_invalid_definition_error'
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
                    'name': 'get_input_one'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_multi_input_early_terminate_pipeline'
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
                            'name': 'retry_multi_input_early_terminate_pipeline'
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
                            'name': 'infinite_loop_pipeline'
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
                            'name': 'materialization_pipeline'
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
                    'name': 'multi'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_multi_output_pipeline'
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
                    'name': 'multiply_by_two'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'dynamic_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'double_total'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'dynamic_pipeline'
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
                            'name': 'dynamic_pipeline'
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
                    'name': 'no_output'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_multi_output_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'child_multi_skip'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'retry_multi_output_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'child_skip'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'retry_multi_output_pipeline'
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
                    'name': 'noop_solid'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'asset_lineage_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'noop_solid'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'more_complicated_config'
                        },
                        'solidHandle': {
                            'handleID': 'noop_solid'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'noop_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'noop_solid'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'partitioned_asset_lineage_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'noop_solid'
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
                            'name': 'pipeline_with_invalid_definition_error'
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
                    'name': 'palp_a'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'partitioned_asset_lineage_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'palp_a'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'palp_b'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'partitioned_asset_lineage_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'palp_b'
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
                            'name': 'retry_multi_output_pipeline'
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
                            'name': 'scalar_output_pipeline'
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
                            'name': 'scalar_output_pipeline'
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
                            'name': 'no_config_chain_pipeline'
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
                            'name': 'no_config_pipeline'
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
                            'name': 'no_config_chain_pipeline'
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
                            'name': 'scalar_output_pipeline'
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
                    'name': 'return_one'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_multi_input_early_terminate_pipeline'
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
                            'name': 'multi_mode_with_loggers'
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
                            'name': 'scalar_output_pipeline'
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
                    'name': 'simple_solid'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'tagged_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'simple_solid'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'solid_asset_a'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'multi_asset_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'solid_asset_a'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'single_asset_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'solid_asset_a'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'solid_asset_b'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'multi_asset_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'solid_asset_b'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'solid_partitioned_asset'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'partitioned_asset_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'solid_partitioned_asset'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'solid_that_gets_tags'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'hello_world_with_tags'
                        },
                        'solidHandle': {
                            'handleID': 'solid_that_gets_tags'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'solid_with_list'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'pipeline_with_list'
                        },
                        'solidHandle': {
                            'handleID': 'solid_with_list'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'solid_with_required_resource'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'required_resource_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'solid_with_required_resource'
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
                            'name': 'spew_pipeline'
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
                            'name': 'retry_resource_pipeline'
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
                    'name': 'sum_inputs'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_multi_input_early_terminate_pipeline'
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
                            'name': 'dynamic_pipeline'
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
                    'name': 'sum_solid'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'csv_hello_world'
                        },
                        'solidHandle': {
                            'handleID': 'sum_solid'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'csv_hello_world_df_input'
                        },
                        'solidHandle': {
                            'handleID': 'sum_solid'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'csv_hello_world_two'
                        },
                        'solidHandle': {
                            'handleID': 'sum_solid'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'csv_hello_world_with_expectations'
                        },
                        'solidHandle': {
                            'handleID': 'sum_solid'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'sum_sq_solid'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'csv_hello_world'
                        },
                        'solidHandle': {
                            'handleID': 'sum_sq_solid'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'csv_hello_world_df_input'
                        },
                        'solidHandle': {
                            'handleID': 'sum_sq_solid'
                        }
                    },
                    {
                        'pipeline': {
                            'name': 'csv_hello_world_with_expectations'
                        },
                        'solidHandle': {
                            'handleID': 'sum_sq_solid'
                        }
                    }
                ]
            },
            {
                '__typename': 'UsedSolid',
                'definition': {
                    'name': 'tag_asset_solid'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'asset_tag_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'tag_asset_solid'
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
                            'name': 'pipeline_with_enum_config'
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
                    'name': 'throw_a_thing'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'naughty_programmer_pipeline'
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
                    'name': 'will_fail'
                },
                'invocations': [
                    {
                        'pipeline': {
                            'name': 'retry_resource_pipeline'
                        },
                        'solidHandle': {
                            'handleID': 'will_fail'
                        }
                    }
                ]
            }
        ]
    }
}
