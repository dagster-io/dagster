SELECT *
FROM {{ ref('sort_by_calories') }}
WHERE type='C'