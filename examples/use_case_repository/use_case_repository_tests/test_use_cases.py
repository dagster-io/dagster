from use_case_repository.snowflake_to_s3_embedded_elt import ingest_s3_to_snowflake, sling_resource


def test_snowflake_to_s3_embedded_elt():
    assert ingest_s3_to_snowflake
    assert sling_resource
