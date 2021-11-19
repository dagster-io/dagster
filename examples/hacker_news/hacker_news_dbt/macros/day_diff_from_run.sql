{% macro day_diff_from_run(start) %}
    DATEDIFF(
        day,
        "{{start}}"::int::timestamp,
        current_date()
    )
{% endmacro %}
