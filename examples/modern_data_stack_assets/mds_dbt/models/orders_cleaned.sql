-- this doesn't really clean anything :P
select * from {{ source('postgres_replica', 'orders') }}