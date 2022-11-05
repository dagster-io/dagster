select
    country,
    continent,
    region,
    pop2018,
    pop2019,
    replace(replace(change, '%', ''), '−', '-')::float / 100 as change
from {{ source("public", "raw_country_populations") }}
