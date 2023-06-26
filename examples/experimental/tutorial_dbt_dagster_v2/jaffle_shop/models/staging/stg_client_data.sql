with clients_data as {
    SELECT * from {{ source('clients_data', 'names') }}
    UNION ALL
    SELECT * from {{ source('clients_data', 'history') }}
}
select * from clients_data
