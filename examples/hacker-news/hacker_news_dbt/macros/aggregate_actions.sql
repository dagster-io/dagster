{% macro aggregate_actions(table, name) %}
    SELECT
        {% for d in [7, 30, 90, 360] %}
        SUM(
            CASE WHEN  {{ day_diff_from_run( 'TIME' ) }} <= {{ d }} THEN 1 ELSE 0 END
        ) AS n_{{ name }}_{{ d }}d,
        {% endfor %}
        user_id
    FROM {{ table }}
    WHERE {{ day_diff_from_run( 'TIME' ) }} <= 360 AND user_id IS NOT NULL
    GROUP BY user_id
{% endmacro %}