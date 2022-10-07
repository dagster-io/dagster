select
    *,
    country_populations["change"].str.rstrip("%").str.replace("−", "-").astype("float") / 100.0 as change
from {{ source("public", "raw_country_populations") }}
