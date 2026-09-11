{#-
    dbt-duckdb does not implement the macros that dbt's `function` materialization dispatches to,
    so building a UDF against duckdb fails out of the box. duckdb does not support
    `CREATE FUNCTION ... RETURNS ... LANGUAGE SQL`, but `CREATE MACRO` is the equivalent, so we
    override the dispatched macros here. This lets these tests actually materialize a dbt function,
    which is what exercises the dbt event streaming code path for function nodes.
-#}

{% macro duckdb__scalar_function_sql(target_relation) %}
    CREATE OR REPLACE MACRO {{ target_relation.render() }} ({{ formatted_scalar_function_args_sql() }}) AS (
        {{ model.compiled_code }}
    )
{% endmacro %}

{% macro duckdb__formatted_scalar_function_args_sql() %}
    {#- duckdb macros are not typed, so the argument data types are dropped here -#}
    {% set args = [] %}
    {% for arg in model.arguments -%}
        {%- do args.append(arg.name) -%}
    {%- endfor %}
    {{ args | join(', ') }}
{% endmacro %}
