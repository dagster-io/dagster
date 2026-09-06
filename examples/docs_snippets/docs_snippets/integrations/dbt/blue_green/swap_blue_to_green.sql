{#
  Promote a freshly-built blue table into green. On Snowflake this is an
  atomic ALTER TABLE ... SWAP WITH — a metadata rename, so consumers see only
  the old or the new table, never a half-built state. On a first publish
  (green doesn't exist yet) it clones blue into green instead.

  Called once per mart by swap_all_marts_if_clean. Warehouses without an
  atomic swap can supply their own implementation (e.g. duckdb__) that
  snapshots green, then CTAS's blue into green's place.
#}
{% macro swap_blue_to_green(model_relation) %}
  {{ return(adapter.dispatch('swap_blue_to_green', 'bluegreen_analytics')(model_relation)) }}
{% endmacro %}


{% macro snowflake__swap_blue_to_green(model_relation) %}
  {% if execute %}
    {% set green = var('green_schema') %}
    {% set blue = var('blue_schema') %}
    {% set db = target.database %}
    {% set tname = model_relation.identifier %}

    {% set green_exists_sql %}
      select count(*)
      from {{ db }}.information_schema.tables
      where table_schema = upper('{{ green }}') and table_name = upper('{{ tname }}')
    {% endset %}
    {% set green_exists = run_query(green_exists_sql).rows[0][0] > 0 %}

    {% if green_exists %}
      {% do log("SWAP " ~ blue ~ "." ~ tname ~ " <-> " ~ green ~ "." ~ tname, info=True) %}
      {% do run_query(
            "alter table " ~ db ~ "." ~ blue ~ "." ~ tname
            ~ " swap with " ~ db ~ "." ~ green ~ "." ~ tname
      ) %}
    {% else %}
      {% do log("First publish of " ~ tname ~ "; promoting blue -> green", info=True) %}
      {% do run_query(
            "create or replace table " ~ db ~ "." ~ green ~ "." ~ tname
            ~ " clone " ~ db ~ "." ~ blue ~ "." ~ tname
      ) %}
    {% endif %}
  {% endif %}
{% endmacro %}
