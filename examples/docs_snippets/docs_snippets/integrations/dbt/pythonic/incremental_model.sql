select
    event_id,
    event_time,
    user_id,
    event_type
from {{ source('app', 'events') }}
{% if is_incremental() %}
    where event_time >= '{{ var("start_date") }}' and event_time < '{{ var("end_date") }}'
{% endif %}
