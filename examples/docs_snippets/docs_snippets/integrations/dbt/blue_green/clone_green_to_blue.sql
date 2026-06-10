{#
  Prep the "blue" staging schema with the current state of "green" before any
  model builds, so incremental models, views, and unselected tables all start
  from the live published data. Runs as on-run-start.

  Dispatched on adapter type: Snowflake clones the whole schema in one
  zero-copy metadata operation. Warehouses without a schema-clone primitive
  can supply their own implementation (e.g. duckdb__) that iterates CTAS
  per table.
#}
{% macro clone_green_to_blue() %}
  {{ return(adapter.dispatch('clone_green_to_blue', 'bluegreen_analytics')()) }}
{% endmacro %}


{% macro snowflake__clone_green_to_blue() %}
  {% if execute %}
    {% set green = var('green_schema') %}
    {% set blue = var('blue_schema') %}
    {% set db = target.database %}

    {% set green_exists_sql %}
      select count(*)
      from {{ db }}.information_schema.schemata
      where schema_name = upper('{{ green }}')
    {% endset %}
    {% set green_exists = run_query(green_exists_sql).rows[0][0] > 0 %}

    {% if not green_exists %}
      {% do log("No " ~ green ~ " schema yet; first publish run.", info=True) %}
      {% do run_query("create schema if not exists " ~ db ~ "." ~ blue) %}
    {% else %}
      {% do run_query(
            "create or replace schema " ~ db ~ "." ~ blue
            ~ " clone " ~ db ~ "." ~ green
      ) %}
    {% endif %}
  {% endif %}
{% endmacro %}
