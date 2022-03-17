select *
from {{ ref('comment_daily_stats') }}
full outer join {{ ref('story_daily_stats') }}
using (date)


