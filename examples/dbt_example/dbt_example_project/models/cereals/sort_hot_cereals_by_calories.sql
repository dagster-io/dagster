select *
from {{ ref('sort_by_calories') }}
where type='H'
