import re
from copy import deepcopy

from .test_expectations import sanitize as sanitize_gql
from .utils import sync_execute_get_events


def sanitize(logs):
    res = deepcopy(logs)
    for log in res:
        if 'message' in log:
            log['message'] = re.sub('(pid: [0-9]*)', '(pid: *****)', log['message'])
            log['message'] = re.sub('in [0-9.]*ms', 'in ***.**ms', log['message'])

    return res


def test_materializations(snapshot):
    logs = sanitize_gql(
        sanitize(
            sync_execute_get_events(
                variables={
                    'executionParams': {
                        'selector': {'name': 'materialization_pipeline'},
                        'mode': 'default',
                    }
                }
            )
        )
    )

    # Remove execution durations from ExecutionStepSuccessEvent messages
    for log in logs:
        if log["__typename"] == "ExecutionStepSuccessEvent":
            log["message"] = re.sub(r'in .*', "in", log["message"])

    materializations = [log for log in logs if log['__typename'] == 'StepMaterializationEvent']
    assert len(materializations) == 1
    mat = materializations[0]['materialization']
    assert mat['label'] == 'all_types'

    text_entry = mat['metadataEntries'][0]
    assert text_entry['__typename'] == 'EventTextMetadataEntry'
    assert text_entry['text']

    text_entry = mat['metadataEntries'][1]
    assert text_entry['__typename'] == 'EventUrlMetadataEntry'
    assert text_entry['url']

    text_entry = mat['metadataEntries'][2]
    assert text_entry['__typename'] == 'EventPathMetadataEntry'
    assert text_entry['path']

    text_entry = mat['metadataEntries'][3]
    assert text_entry['__typename'] == 'EventJsonMetadataEntry'
    assert text_entry['jsonString']

    text_entry = mat['metadataEntries'][4]
    assert text_entry['__typename'] == 'EventPythonArtifactMetadataEntry'
    assert text_entry['module']
    assert text_entry['name']

    text_entry = mat['metadataEntries'][5]
    assert text_entry['__typename'] == 'EventPythonArtifactMetadataEntry'
    assert text_entry['module']
    assert text_entry['name']

    snapshot.assert_match(logs)
