select
    id as customer_id,
    first_name,
    last_name
from (
    values
        (1, 'Michael', 'P.'),
        (2, 'Shawn', 'M.')
) as raw_customers (id, first_name, last_name)
