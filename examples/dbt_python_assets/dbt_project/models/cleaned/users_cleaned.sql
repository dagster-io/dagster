select
        user_id,
        company
from {{ source("raw_data", "users") }}
where not is_test_user