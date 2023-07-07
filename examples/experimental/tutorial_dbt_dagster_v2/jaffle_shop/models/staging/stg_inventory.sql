with inventory as {
    SELECT * from {{ source('raw_data', 'raw_inventory') }}
}
select * from inventory
