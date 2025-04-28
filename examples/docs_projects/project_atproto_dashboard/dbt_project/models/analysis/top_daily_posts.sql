WITH distinct_posts AS (
    SELECT DISTINCT ON (author_handle, post_text, date_trunc('day', created_at))
        author_handle,
        post_text,
        likes,
        quotes,
        replies,
        image_url,
        external_embed_link,
        external_embed_thumbnail,
        external_embed_description,
        created_at
    FROM {{ ref("latest_feed") }}
),

scored_posts AS (
    SELECT
        *,
        (likes * 0.2) + (quotes * 0.4) + (replies * 0.4) AS engagement_score,
        date_trunc('day', created_at) AS post_date,
        row_number() OVER (
            PARTITION BY date_trunc('day', created_at)
            ORDER BY (likes * 0.2) + (quotes * 0.4) + (replies * 0.4) DESC
        ) AS daily_rank
    FROM distinct_posts
),

final AS (
    SELECT
        post_date,
        author_handle,
        post_text,
        likes,
        quotes,
        replies,
        image_url,
        external_embed_link,
        external_embed_thumbnail,
        external_embed_description,
        round(engagement_score, 2) AS engagement_score,
        daily_rank
    FROM scored_posts
    WHERE daily_rank <= 10
)

SELECT * FROM final
