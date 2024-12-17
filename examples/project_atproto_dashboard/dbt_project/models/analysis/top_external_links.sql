WITH distinct_posts AS (
    SELECT DISTINCT ON (author_handle, post_text, date_trunc('day', created_at))
        author_handle,
        post_text,
        likes,
        quotes,
        replies,
        created_at,
        image_url,
        embed,
        external_embed_link,
        external_embed_thumbnail,
        external_embed_description,
        CASE
            WHEN external_embed_link LIKE '%youtu%' THEN 'YouTube'
            WHEN external_embed_link LIKE '%docs%' THEN 'Docs'
            WHEN external_embed_link LIKE '%github%' THEN 'GitHub'
            WHEN external_embed_link LIKE '%substack%' THEN 'SubStack'
            WHEN external_embed_link LIKE '%twitch%' THEN 'Twitch'
            WHEN external_embed_link LIKE '%msnbc%' THEN 'News'
            WHEN external_embed_link LIKE '%theguardian%' THEN 'News'
            WHEN external_embed_link LIKE '%foreignpolicy%' THEN 'News'
            WHEN external_embed_link LIKE '%nytimes%' THEN 'News'
            WHEN external_embed_link LIKE '%wsj%' THEN 'News'
            WHEN external_embed_link LIKE '%bloomberg%' THEN 'News'
            WHEN external_embed_link LIKE '%theverge%' THEN 'News'
            WHEN external_embed_link LIKE '%cnbc%' THEN 'News'
            WHEN external_embed_link LIKE '%.ft.%' THEN 'News'
            WHEN external_embed_link LIKE '%washingtonpost%' THEN 'News'
            WHEN external_embed_link LIKE '%newrepublic%' THEN 'News'
            WHEN external_embed_link LIKE '%huffpost%' THEN 'News'
            WHEN external_embed_link LIKE '%wired%' THEN 'News'
            WHEN external_embed_link LIKE '%medium%' THEN 'Medium'
            WHEN external_embed_link LIKE '%reddit%' THEN 'Reddit'
            WHEN external_embed_link LIKE '%/blog/%' THEN 'Blog'
            ELSE 'Other'
        END AS external_link_type
    FROM {{ ref("latest_feed") }}
    WHERE external_embed_link IS NOT null
),

scored_posts AS (
    SELECT
        *,
        (likes * 0.2) + (quotes * 0.4) + (replies * 0.4) AS engagement_score,
        date_trunc('day', created_at) AS post_date,
        row_number() OVER (
            PARTITION BY date_trunc('day', created_at), external_link_type
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
        round(engagement_score, 2) AS engagement_score,
        daily_rank,
        embed,
        external_embed_link,
        external_embed_thumbnail,
        external_embed_description,
        external_link_type
    FROM scored_posts
    WHERE daily_rank <= 10
)

SELECT * FROM final
