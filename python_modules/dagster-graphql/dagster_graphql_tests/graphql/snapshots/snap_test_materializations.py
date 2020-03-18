# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_materializations 1'] = [
    {
        '__typename': 'PipelineStartEvent',
        'level': 'DEBUG',
        'message': 'Started execution of pipeline "materialization_pipeline".',
        'step': None
    },
    {
        '__typename': 'EngineEvent',
        'level': 'DEBUG',
        'message': 'Executing steps in process ((pid: *****))',
        'step': None
    },
    {
        '__typename': 'ExecutionStepStartEvent',
        'level': 'DEBUG',
        'message': 'Started execution of step "materialize.compute".',
        'step': {
            'key': 'materialize.compute',
            'kind': 'COMPUTE',
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
                },
                {
                    '__typename': 'EventPythonArtifactMetadataEntry',
                    'description': None,
                    'label': 'python class',
                    'module': 'dagster.core.definitions.events',
                    'name': 'EventMetadataEntry'
                },
                {
                    '__typename': 'EventPythonArtifactMetadataEntry',
                    'description': None,
                    'label': 'python function',
                    'module': 'dagster.utils',
                    'name': 'file_relative_path'
                }
            ]
        },
        'message': 'a materialization with all metadata types',
        'step': {
            'key': 'materialize.compute',
            'solidHandleID': 'materialize'
        }
    },
    {
        '__typename': 'ExecutionStepOutputEvent',
        'level': 'DEBUG',
        'message': 'Yielded output "result" of type "Any". (Type check passed).',
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
        'message': 'Finished execution of step "materialize.compute" in',
        'step': {
            'key': 'materialize.compute',
            'solidHandleID': 'materialize'
        }
    },
    {
        '__typename': 'EngineEvent',
        'level': 'DEBUG',
        'message': 'Finished steps in process ((pid: *****)) in ***.**ms',
        'step': None
    },
    {
        '__typename': 'PipelineSuccessEvent',
        'level': 'DEBUG',
        'message': 'Finished execution of pipeline "materialization_pipeline".',
        'step': None
    }
]
