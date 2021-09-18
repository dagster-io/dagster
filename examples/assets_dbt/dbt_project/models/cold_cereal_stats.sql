SELECT
    name,
    protein_per_calorie,
    fat_per_calorie
FROM {{ ref('cereal_stats') }}
WHERE type = 'C'
