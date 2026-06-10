{#
  on-run-end hook for the blue/green flow.

  Promotes every mart from blue to green ONLY if every node in the run
  finished cleanly (models built, tests passed, nothing skipped or errored).
  If anything failed, blue keeps the un-promoted data and green is left
  untouched — fix the issue and re-run, and the next clean run promotes.

  Why on-run-end and not a per-model post-hook: post-hook fires when a model's
  SQL finishes but BEFORE dbt runs the tests attached to that model. Promoting
  in a post-hook would swap a bad model into green before its own unique /
  not_null tests had a chance to fail. on-run-end is the first hook point where
  every model and every test has finished and the `results` array is populated
  with each node's status.

  dbt invokes on-run-end whenever the run finishes, INCLUDING when models or
  tests failed (failures live in `results`, not as raised exceptions). It is
  skipped only on catastrophic errors (parse failure, on-run-start raising, the
  process being killed) — in which case nothing was published anyway.
#}
{% macro swap_all_marts_if_clean() %}
  {% if execute %}
    {% if results is not defined or results | length == 0 %}
      {% do log("No node results available — nothing to swap.", info=True) %}
      {{ return("") }}
    {% endif %}

    {# Abort the entire promotion if any node did not succeed or pass. #}
    {% set failures = [] %}
    {% for r in results %}
      {% if r.status not in ['success', 'pass'] %}
        {% do failures.append(r.node.unique_id ~ " (" ~ r.status ~ ")") %}
      {% endif %}
    {% endfor %}

    {% if failures | length > 0 %}
      {% do log(
          "Build had " ~ failures | length ~ " failure(s); skipping swap. "
          ~ "Blue holds the un-promoted data. Failed nodes: "
          ~ failures | join(", "),
          info=True
      ) %}
      {{ return("") }}
    {% endif %}

    {# Clean run: promote every mart. #}
    {% set marts_swapped = [] %}
    {% for r in results %}
      {% if r.node.resource_type == 'model' and 'marts' in r.node.fqn %}
        {% do swap_blue_to_green(r.node) %}
        {% do marts_swapped.append(r.node.name) %}
      {% endif %}
    {% endfor %}

    {% do log(
        "Swap complete; promoted " ~ marts_swapped | length ~ " mart(s) to green: "
        ~ marts_swapped | join(", "),
        info=True
    ) %}
  {% endif %}
{% endmacro %}
