# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_start_subplan_invalid_output_path 1'] = {
    'startSubplanExecution': {
        '__typename': 'StartSubplanExecutionSuccess',
        'hasFailures': True,
        'pipeline': {
            'name': 'pandas_hello_world'
        },
        'stepResults': [
            {
                '__typename': 'StepSuccessResult',
                'outputName': 'unmarshal-input-output',
                'step': {
                    'key': 'sum_solid.transform.unmarshal-input.num'
                },
                'success': True,
                'valueRepr': '''   num1  num2
0     1     2
1     3     4'''
            },
            {
                '__typename': 'StepSuccessResult',
                'outputName': 'result',
                'step': {
                    'key': 'sum_solid.transform'
                },
                'success': True,
                'valueRepr': '''   num1  num2  sum
0     1     2    3
1     3     4    7'''
            },
            {
                '__typename': 'StepFailureResult',
                'errorMessage': 'Error occured during step sum_solid.transform.marshal-output.result',
                'step': {
                    'key': 'sum_solid.transform.marshal-output.result'
                },
                'success': False
            }
        ]
    }
}
