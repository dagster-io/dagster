from .utils import sync_execute_get_events


def test_materializations(snapshot):
    logs = sync_execute_get_events(
        variables={
            'executionParams': {'selector': {'name': 'materialization_pipeline'}, 'mode': 'default'}
        }
    )
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

    snapshot.assert_match(logs)
