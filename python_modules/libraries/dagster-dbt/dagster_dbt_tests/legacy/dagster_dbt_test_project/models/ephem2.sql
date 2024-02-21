{{config(materialized="ephemeral")}}
select * from {{ref("ephem1")}}