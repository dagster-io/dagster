WITH max_update as (
	SELECT 
		max(strptime(regexp_extract(filename, 'dagster-demo/atproto_actor_feed_snapshot/(\d{4}-\d{2}-\d{2}/\d{2}/\d{2})', 1), '%Y-%m-%d/%H/%M')) as max_extracted_timestamp,
	    regexp_extract(filename, 'did:(.*?)\.json') as profile_id
	FROM {{ref("stg_feed_snapshots")}}
	GROUP BY
		regexp_extract(filename, 'did:(.*?)\.json')
)

SELECT 
	sfs.json.post.author.handle as author_handle,
    CAST(sfs.json.post.like_count as int) as likes,
    CAST(sfs.json.post.quote_count as int) as quotes,
    CAST(sfs.json.post.reply_count as int) as replies,
    sfs.json.post.record.text as post_text,
    cast(sfs.json.post.record.created_at as timestamp) as created_at,
	max_update.max_extracted_timestamp,
	max_update.profile_id
FROM {{ref("stg_feed_snapshots")}} sfs
JOIN max_update
	ON max_update.profile_id = regexp_extract(sfs.filename, 'did:(.*?)\.json')
	AND max_update.max_extracted_timestamp = strptime(regexp_extract(sfs.filename, 'dagster-demo/atproto_actor_feed_snapshot/(\d{4}-\d{2}-\d{2}/\d{2}/\d{2})', 1), '%Y-%m-%d/%H/%M')
