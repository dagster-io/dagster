{{config(materialized="ephemeral")}}
select * from {{ref("sort_by_calories")}}