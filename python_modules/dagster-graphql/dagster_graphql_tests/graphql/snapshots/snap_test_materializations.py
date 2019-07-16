# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_materializations 1'] = [
    {
        '__typename': 'PipelineStartEvent',
        'level': 'DEBUG',
        'message': 'DagsterEventType.PIPELINE_START for pipeline materialization_pipeline',
        'step': None
    },
    {
        '__typename': 'ExecutionStepStartEvent',
        'level': 'DEBUG',
        'message': 'DagsterEventType.STEP_START for step materialize.compute',
        'step': {
            'key': 'materialize.compute',
            'kind': 'COMPUTE',
            'solidHandleID': 'materialize'
        }
    },
    {
        '__typename': 'LogMessageEvent',
        'level': 'INFO',
        'message': "Solid 'materialize' materialized 'all_types'",
        'step': {
            'key': 'materialize.compute',
            'solidHandleID': 'materialize'
        }
    },
    {
        '__typename': 'StepMaterializationEvent',
        'level': 'DEBUG',
        'materialization': {
            'description': 'a materialization with all metadata types',
            'label': 'all_types',
            'metadataEntries': [
                {
                    '__typename': 'EventTextMetadataEntry',
                    'description': None,
                    'label': 'text',
                    'text': 'text is cool'
                },
                {
                    '__typename': 'EventUrlMetadataEntry',
                    'description': None,
                    'label': 'url',
                    'url': 'https://bigty.pe/neato'
                },
                {
                    '__typename': 'EventPathMetadataEntry',
                    'description': None,
                    'label': 'path',
                    'path': '/tmp/awesome'
                },
                {
                    '__typename': 'EventJsonMetadataEntry',
                    'description': None,
                    'jsonString': '{"is_dope": true}',
                    'label': 'json'
                }
            ]
        },
        'message': 'DagsterEventType.STEP_MATERIALIZATION for step materialize.compute',
        'step': {
            'key': 'materialize.compute',
            'solidHandleID': 'materialize'
        }
    },
    {
        '__typename': 'LogMessageEvent',
        'level': 'INFO',
        'message': "Solid 'materialize' emitted output 'result'",
        'step': {
            'key': 'materialize.compute',
            'solidHandleID': 'materialize'
        }
    },
    {
        '__typename': 'ExecutionStepOutputEvent',
        'level': 'DEBUG',
        'message': 'DagsterEventType.STEP_OUTPUT for step materialize.compute',
        'outputName': 'result',
        'step': {
            'key': 'materialize.compute',
            'kind': 'COMPUTE',
            'solidHandleID': 'materialize'
        },
        'typeCheck': {
            'description': None,
            'label': 'result',
            'metadataEntries': [
            ]
        }
    },
    {
        '__typename': 'ExecutionStepSuccessEvent',
        'level': 'DEBUG',
        'message': 'DagsterEventType.STEP_SUCCESS for step materialize.compute',
        'step': {
            'key': 'materialize.compute',
            'solidHandleID': 'materialize'
        }
    },
    {
        '__typename': 'PipelineSuccessEvent',
        'level': 'DEBUG',
        'message': 'DagsterEventType.PIPELINE_SUCCESS for pipeline materialization_pipeline',
        'step': None
    }
]
