SELECT
    DISTINCT c.table_name as "table_name",
        c.column_name as "column name",
        c.classifiers
    FROM
        sdf.information_schema.columns c
    WHERE
        CONTAINS_ARRAY_VARCHAR(c.classifiers, '%DATA.pii%')
        and c.table_id like '%lineage.pub.sink'