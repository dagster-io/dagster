SELECT 
    c.table_id
FROM 
    sdf.information_schema.columns c
WHERE 
    CONTAINS_ARRAY_VARCHAR(c.classifiers, 'PII')
    AND c.schema_name = 'external'
GROUP BY c.table_id;
