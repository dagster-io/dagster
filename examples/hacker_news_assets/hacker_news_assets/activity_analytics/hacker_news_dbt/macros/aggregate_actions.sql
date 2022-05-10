{% macro aggregate_actions(table) %}
    SELECT
        COUNT(*) as num_actions,
        "by"
    FROM {{ table }}
    WHERE "by" IS NOT NULL
    GROUP BY "by"
{% endmacro %}