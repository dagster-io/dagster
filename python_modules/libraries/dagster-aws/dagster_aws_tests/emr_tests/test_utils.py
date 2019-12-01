from dagster_aws.emr.utils import subset_environment_dict


def test_subset_environment_dict():
    environment_dict = {
        'solids': {'blah': {'config': {'foo': 'a string', 'bar': 123}}},
        'resources': {
            'pyspark': {
                'config': {
                    'pipeline_file': 'dagster_aws_tests/emr_tests/test_pyspark.py',
                    'pipeline_fn_name': 'pipe',
                    'cluster_id': 'j-272P42200OZ0Q',
                    'staging_bucket': 'dagster-scratch-80542c2',
                    'region_name': 'us-west-1',
                }
            }
        },
    }
    res = subset_environment_dict(environment_dict, 'blah')
    assert res == environment_dict

    res = subset_environment_dict(environment_dict, 'not_here')
    assert res['solids'] == {}
