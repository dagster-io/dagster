{{ config(tags=["bar"]) }}
SELECT * from {{ ref('sort_by_calories') }} LIMIT 1