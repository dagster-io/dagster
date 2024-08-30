select
    id as customer_id,
    first_name,
    last_name
from {{ source('raw', 'raw_customers') }}     # Define the raw_customers asset as a source