with raw as (
    select * from read_ndjson_objects(
        'r2://dagster-demo/atproto_starter_pack_snapshot/2024-11-22/13/01/at://did:plc:lc5jzrr425fyah724df3z5ik/app.bsky.graph.starterpack/3l7cddlz5ja24.json'
    )
)
select json.subject.did from raw