select
        (_airbyte_data->'index')::int as index,
        (_airbyte_data->'user_id')::int as user_id,
        (_airbyte_data->'is_bot')::bool as is_bot
from {{ source('postgres_replica', 'users') }}