{% macro log_columns_in_relation() %}
    {%- set is_dagster_dbt_cli = env_var('DAGSTER_DBT_CLI', '') == 'true' -%}
    {%- set columns = adapter.get_columns_in_relation(this) -%}
    {%- set table_schema = {} -%}

    {% for column in columns %}
        {%- set serializable_column = {column.name: {'data_type': column.data_type}} -%}
        {%- set _ = table_schema.update(serializable_column) -%}
    {% endfor %}

    {% if is_dagster_dbt_cli and table_schema %}
        {% do log(tojson(table_schema), info=true) %}
    {% endif %}
{% endmacro %}
