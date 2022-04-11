select
        (_airbyte_data->'index')::int as index,
        (_airbyte_data->'user_id')::int as user_id,
        TO_TIMESTAMP(_airbyte_data->>'order_time', 'YYYY-MM-DDTHH:MI:SSZ') as order_time,
        (_airbyte_data->'order_value')::float as order_value
from {{ source('postgres_replica', 'orders') }}