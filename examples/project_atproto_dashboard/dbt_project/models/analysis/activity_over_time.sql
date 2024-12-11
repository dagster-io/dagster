With final as(
    SELECT 
        date_trunc('day', created_at) as post_date,
        COUNT(DISTINCT post_text) as unique_posts,
        COUNT(DISTINCT author_handle) as active_authors,
        SUM(likes) as total_likes,
        SUM(replies) as total_comments,
        SUM(quotes) as total_quotes
    FROM {{ref("latest_feed")}}  lf 
    GROUP BY date_trunc('day', created_at)
    ORDER BY date_trunc('day', created_at) DESC
)
SELECT * FROM final