select *
from {{ ref('sort_by_calories') }}
limit 1
