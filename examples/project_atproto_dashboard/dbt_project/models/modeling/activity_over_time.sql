WITH final AS (
    SELECT
        date_trunc('day', created_at) AS post_date,
        count(DISTINCT post_text) AS unique_posts,
        count(DISTINCT author_handle) AS active_authors,
        sum(likes) AS total_likes,
        sum(replies) AS total_comments,
        sum(quotes) AS total_quotes
    FROM {{ ref("latest_feed") }}
    GROUP BY date_trunc('day', created_at)
    ORDER BY date_trunc('day', created_at) DESC
)

SELECT * FROM final
