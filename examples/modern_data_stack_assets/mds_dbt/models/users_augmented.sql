-- ok, it doesn't actually augment anything ;)
select * from {{ source('postgres_replica', 'users') }}