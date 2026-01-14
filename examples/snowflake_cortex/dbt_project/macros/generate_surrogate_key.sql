{% macro generate_surrogate_key(field_list) -%}
    {{ return(adapter.dispatch('generate_surrogate_key', 'dbt_utils')(field_list)) }}
{%- endmacro %}
