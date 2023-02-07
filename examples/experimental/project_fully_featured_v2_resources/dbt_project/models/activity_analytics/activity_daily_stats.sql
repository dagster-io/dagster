SELECT *
FROM {{ ref('comment_daily_stats') }}
FULL OUTER JOIN {{ ref('story_daily_stats') }}
USING (date)
