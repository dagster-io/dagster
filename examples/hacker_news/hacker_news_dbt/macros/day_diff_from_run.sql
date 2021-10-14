{% macro day_diff_from_run(start) %}
    DATEDIFF(
        day,
        "{{start}}"::timestamp,
        '{{ var("run_date") }}'::timestamp
    )
{% endmacro %}
