select
    continent,
    sum(pop2019) as pop2019,
    average(change) as change
from {{ ref("country_populations") }}
group by continent
