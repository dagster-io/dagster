{{ config(tags=["foo", "bar"]) }}
SELECT *
from {{ ref("cereals") }}
ORDER BY calories