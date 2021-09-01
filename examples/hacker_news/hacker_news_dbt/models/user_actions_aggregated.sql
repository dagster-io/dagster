{{ config(materialized='table') }}
SELECT * FROM {{ ref('comments_agg') }} FULL OUTER JOIN {{ ref('stories_agg') }} USING ("by")
