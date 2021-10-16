{% macro day_diff_from_run(start) %}
    DATEDIFF(
        day,
        "{{start}}"::timestamp,
        current_date()
    )
{% endmacro %}
