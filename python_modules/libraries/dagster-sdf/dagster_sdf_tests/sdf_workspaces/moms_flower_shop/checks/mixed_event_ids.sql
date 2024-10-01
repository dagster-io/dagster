SELECT
    DISTINCT c.table_name as "table_name",
    c.column_name as "column name",
    c.classifiers
FROM
    sdf.information_schema.columns c
WHERE
    -- more than one EVENT classifier is assigned
    CAST(c.classifiers AS VARCHAR) LIKE '%EVENT%EVENT%'