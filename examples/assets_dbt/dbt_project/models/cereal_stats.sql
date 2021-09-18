SELECT
    name,
    type,
    protein / calories as protein_per_calorie,
    fat / calories as fat_per_calorie
FROM cereals
