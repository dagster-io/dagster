# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_successful_one_part_execute_plan 1'] = {
    'executePlan': {
        '__typename': 'ExecutePlanSuccess',
        'hasFailures': False,
        'pipeline': {
            'name': 'csv_hello_world'
        },
        'stepEvents': [
            {
                '__typename': 'ExecutionStepStartEvent',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepInputEvent',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            },
            {
                '__typename': 'ExecutionStepOutputEvent',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                },
                'valueRepr': "[OrderedDict([('num1', '1'), ('num2', '2'), ('sum', 3)]), OrderedDict([('num1', '3'), ('num2', '4'), ('sum', 7)])]"
            },
            {
                '__typename': 'ExecutionStepSuccessEvent',
                'step': {
                    'key': 'sum_solid.compute',
                    'metadata': [
                    ]
                }
            }
        ]
    }
}
