{% macro dagster__log_columns_in_relation() %}
    {%- set columns = adapter.get_columns_in_relation(this) -%}
    {%- set table_schema = {} -%}

    {% for column in columns %}
        {%- set serializable_column = {column.name: {'data_type': column.data_type}} -%}
        {%- set _ = table_schema.update(serializable_column) -%}
    {% endfor %}

    {% do log(tojson(table_schema), info=true) %}
{% endmacro %}
