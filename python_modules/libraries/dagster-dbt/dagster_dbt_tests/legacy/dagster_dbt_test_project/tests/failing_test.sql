select * from {{ref("sort_by_calories")}}
where {{var("fail_test", "false")}}