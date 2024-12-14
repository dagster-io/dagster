WITH distinct_posts AS (
  SELECT 
    DISTINCT ON (author_handle, post_text, date_trunc('day', created_at))
    author_handle,
    post_text,
    likes,
    quotes,
    replies,
    created_at,
    embed,
    external_embed_link,
    external_embed_thumbnail,
    external_embed_description,
    CASE 
	  	WHEN external_embed_link like '%youtu%' THEN 'YouTube'
	  	WHEN external_embed_link like '%docs%' THEN 'Docs'
	  	WHEN external_embed_link like '%github%' THEN 'GitHub'
	  	WHEN external_embed_link like '%substack%' THEN 'SubStack'
	  	WHEN external_embed_link like '%twitch%' THEN 'Twitch'
	  	WHEN external_embed_link like '%msnbc%' THEN 'News'
	  	WHEN external_embed_link like '%theguardian%' THEN 'News'
	  	WHEN external_embed_link like '%foreignpolicy%' THEN 'News'
	  	WHEN external_embed_link like '%nytimes%' THEN 'News'
	  	WHEN external_embed_link like '%wsj%' THEN 'News'
	  	WHEN external_embed_link like '%bloomberg%' THEN 'News'
	  	WHEN external_embed_link like '%theverge%' THEN 'News'
	  	WHEN external_embed_link like '%cnbc%' THEN 'News'
	  	WHEN external_embed_link like '%.ft.%' THEN 'News'
	  	WHEN external_embed_link like '%washingtonpost%' THEN 'News'
	  	WHEN external_embed_link like '%newrepublic%' THEN 'News'
	  	WHEN external_embed_link like '%huffpost%' THEN 'News'
	  	WHEN external_embed_link like '%huffpost%' THEN 'News'
	  	WHEN external_embed_link like '%wired%' THEN 'News'
	  	WHEN external_embed_link like '%medium%' THEN 'Medium'
	  	WHEN external_embed_link like '%reddit%' THEN 'Reddit'
	  	WHEN external_embed_link like '%/blog/%' THEN 'Blog'
  		Else 'Other' 
  	END as external_link_type
  FROM {{ref("latest_feed")}} 
  WHERE external_embed_link is not null
),
scored_posts AS (
  SELECT 
    *,
    (likes * 0.2) + (quotes * 0.4) + (replies * 0.4) as engagement_score,
    date_trunc('day', created_at) as post_date,
    ROW_NUMBER() OVER (
      PARTITION BY date_trunc('day', created_at), external_link_type
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