{% macro aggregate_actions(table, name) %}
    SELECT
        {% for d in [7, 30, 90, 360] %}
        SUM(
            CASE WHEN  {{ day_diff_from_run( 'time' ) }} <= {{ d }} THEN 1 ELSE 0 END
        ) AS n_{{ name }}_{{ d }}d,
        {% endfor %}
        "by"
    FROM {{ table }}
    WHERE {{ day_diff_from_run( 'time' ) }} <= 360 AND "by" IS NOT NULL
    GROUP BY "by"
{% endmacro %}