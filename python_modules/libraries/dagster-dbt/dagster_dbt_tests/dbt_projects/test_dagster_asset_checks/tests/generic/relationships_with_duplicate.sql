{% test relationships_with_duplicate(model, column_name, field, to, another_to) %}

with parent as (

    select
        {{ field }} as id

    from {{ to }}

),

duplicate_parent as (

    select
        {{ field }} as id

    from {{ another_to }}

),

child as (

    select
        {{ column_name }} as id

    from {{ model }}

)

select *
from child
where id is not null
  and id not in (select id from parent)
  and id not in (select id from duplicate_parent)

{% endtest %}
