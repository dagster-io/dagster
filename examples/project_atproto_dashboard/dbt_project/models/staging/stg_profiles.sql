with raw as (
    select * from read_ndjson_objects(
        'r2://dagster-demo/atproto_starter_pack_snapshot/**/*.json', filename=true)
)

Select * from raw