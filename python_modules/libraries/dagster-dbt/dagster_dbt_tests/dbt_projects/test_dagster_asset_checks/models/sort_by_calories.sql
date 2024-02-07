{{ config(tags=["foo", "bar"]) }}
SELECT *
from {{ ref("raw_cereals") }}
ORDER BY calories