WITH distinct_posts AS (
  SELECT 
    DISTINCT ON (author_handle, post_text, date_trunc('day', created_at))
    author_handle,
    post_text,
    likes,
    quotes,
    replies,
    created_at
  FROM {{ref("latest_feed")}} 
),
scored_posts AS (
  SELECT 
    *,
    (likes * 0.2) + (quotes * 0.4) + (replies * 0.4) as engagement_score,
    date_trunc('day', created_at) as post_date,
    ROW_NUMBER() OVER (
      PARTITION BY date_trunc('day', created_at) 
      ORDER BY (likes * 0.2) + (quotes * 0.4) + (replies * 0.4) DESC
    ) as daily_rank
  FROM distinct_posts
),
final as (
  SELECT 
    post_date,
    author_handle,
    post_text,
    likes,
    quotes,
    replies,
    ROUND(engagement_score, 2) as engagement_score,
    daily_rank
  FROM scored_posts
  WHERE daily_rank <= 10
)
SELECT * FROM final