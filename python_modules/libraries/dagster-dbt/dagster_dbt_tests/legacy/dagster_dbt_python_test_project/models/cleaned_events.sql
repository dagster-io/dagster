{{ config(tags=["events"]) }}
SELECT * from {{ source('raw_data', 'events') }}