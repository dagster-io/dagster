# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_basic_pipeline_execution_plan_serialization 1'] = {
    'deps': {
        'add_one.transform': [
            'return_one.transform'
        ],
        'return_one.transform': [
        ]
    },
    'step_metas': [
        {
            'key': 'return_one.transform',
            'solid_name': 'return_one',
            'step_input_metas': [
            ],
            'step_kind_data': {
            },
            'step_output_metas': [
                {
                    'dagster_type_name': 'Int',
                    'name': 'result'
                }
            ],
            'tag': 'TRANSFORM'
        },
        {
            'key': 'add_one.transform',
            'solid_name': 'add_one',
            'step_input_metas': [
                {
                    'dagster_type_name': 'Int',
                    'name': 'num',
                    'prev_output_handle': {
                        'output_name': 'result',
                        'step_key': 'return_one.transform'
                    }
                }
            ],
            'step_kind_data': {
            },
            'step_output_metas': [
                {
                    'dagster_type_name': 'Int',
                    'name': 'result'
                }
            ],
            'tag': 'TRANSFORM'
        }
    ]
}

snapshots['test_execution_plan_with_expectations 1'] = {
    'deps': {
        'add_one.num.expectation.positive': [
            'return_one.transform'
        ],
        'add_one.output.num.expectations.join': [
            'add_one.num.expectation.positive'
        ],
        'add_one.transform': [
            'add_one.output.num.expectations.join'
        ],
        'return_one.transform': [
        ]
    },
    'step_metas': [
        {
            'key': 'return_one.transform',
            'solid_name': 'return_one',
            'step_input_metas': [
            ],
            'step_kind_data': {
            },
            'step_output_metas': [
                {
                    'dagster_type_name': 'Int',
                    'name': 'result'
                }
            ],
            'tag': 'TRANSFORM'
        },
        {
            'key': 'add_one.num.expectation.positive',
            'solid_name': 'add_one',
            'step_input_metas': [
                {
                    'dagster_type_name': 'Int',
                    'name': 'expectation_input',
                    'prev_output_handle': {
                        'output_name': 'result',
                        'step_key': 'return_one.transform'
                    }
                }
            ],
            'step_kind_data': {
                'expectation_name': 'positive',
                'input_name': 'num'
            },
            'step_output_metas': [
                {
                    'dagster_type_name': 'Int',
                    'name': 'expectation_value'
                }
            ],
            'tag': 'INPUT_EXPECTATION'
        },
        {
            'key': 'add_one.output.num.expectations.join',
            'solid_name': 'add_one',
            'step_input_metas': [
                {
                    'dagster_type_name': 'Int',
                    'name': 'add_one.num.expectation.positive',
                    'prev_output_handle': {
                        'output_name': 'expectation_value',
                        'step_key': 'add_one.num.expectation.positive'
                    }
                }
            ],
            'step_kind_data': {
            },
            'step_output_metas': [
                {
                    'dagster_type_name': 'Int',
                    'name': 'join_output'
                }
            ],
            'tag': 'JOIN'
        },
        {
            'key': 'add_one.transform',
            'solid_name': 'add_one',
            'step_input_metas': [
                {
                    'dagster_type_name': 'Int',
                    'name': 'num',
                    'prev_output_handle': {
                        'output_name': 'join_output',
                        'step_key': 'add_one.output.num.expectations.join'
                    }
                }
            ],
            'step_kind_data': {
            },
            'step_output_metas': [
                {
                    'dagster_type_name': 'Int',
                    'name': 'result'
                }
            ],
            'tag': 'TRANSFORM'
        }
    ]
}

snapshots['test_execution_step_meta 1'] = {
    'key': 'step_key',
    'solid_name': 'some_solid',
    'step_input_metas': [
        {
            'dagster_type_name': 'Int',
            'name': 'input_one',
            'prev_output_handle': {
                'output_name': 'some_output',
                'step_key': 'prev_step'
            }
        }
    ],
    'step_kind_data': {
    },
    'step_output_metas': [
        {
            'dagster_type_name': 'String',
            'name': 'output_one'
        }
    ],
    'tag': 'TRANSFORM'
}

snapshots['test_execution_plan_meta 1'] = {
    'deps': {
        'something': [
            'something_else'
        ]
    },
    'step_metas': [
        {
            'key': 'step_key',
            'solid_name': 'some_solid',
            'step_input_metas': [
                {
                    'dagster_type_name': 'Int',
                    'name': 'input_one',
                    'prev_output_handle': {
                        'output_name': 'some_output',
                        'step_key': 'prev_step'
                    }
                }
            ],
            'step_kind_data': {
            },
            'step_output_metas': [
                {
                    'dagster_type_name': 'String',
                    'name': 'output_one'
                }
            ],
            'tag': 'TRANSFORM'
        }
    ]
}
