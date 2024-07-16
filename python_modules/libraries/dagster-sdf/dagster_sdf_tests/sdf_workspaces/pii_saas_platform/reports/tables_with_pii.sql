SELECT 
  t.table_id, 
  t.description, 
  t.dialect
FROM 
  sdf.information_schema.tables t
JOIN 
  sdf.information_schema.columns c ON t.table_id = c.table_id
WHERE CONTAINS_ARRAY_VARCHAR(c.classifiers, 'PII')
GROUP BY 1,2,3;