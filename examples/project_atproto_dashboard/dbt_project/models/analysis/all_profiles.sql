With max_profile_data as (
	SELECT
		json_extract_string(json, '$.subject.did') as profile_did,
		max(strptime(regexp_extract(filename, 'dagster-demo/atproto_starter_pack_snapshot/(\d{4}-\d{2}-\d{2}/\d{2}/\d{2})', 1), '%Y-%m-%d/%H/%M')) as max_extracted_timestamp
	FROM {{ref("stg_profiles")}}
	GROUP BY
		json_extract_string(json, '$.subject.did')
),
profiles as (
	SELECT 
		json_extract_string(json, '$.subject.handle') as handle_subject,
		json_extract_string(json, '$.subject.did') as profile_did,
		json_extract_string(json, '$.subject.avatar') as profile_avatar,
		json_extract_string(json, '$.subject.display_name') as profile_display_name,
		json_extract_string(json, '$.subject.created_at') as profile_created_date,
		json_extract_string(json, '$.subject.description') as profile_description
	FROM {{ref("stg_profiles")}} stg_prof
	JOIN max_profile_data
		ON json_extract_string(stg_prof.json, '$.subject.did') = max_profile_data.profile_did
		AND strptime(regexp_extract(stg_prof.filename, 'dagster-demo/atproto_starter_pack_snapshot/(\d{4}-\d{2}-\d{2}/\d{2}/\d{2})', 1), '%Y-%m-%d/%H/%M') = max_profile_data.max_extracted_timestamp
),
user_aggregates as (
	SELECT 
		REPLACE(author_handle, '"', '') as author_handle,
		COUNT(*) as num_posts,
		AVG(cast(lf.likes as int)) as average_likes,
		SUM(cast(lf.likes as int)) as total_likes,
		SUM(cast(lf.replies as int)) as total_replies,
		SUM(cast(lf.likes as int))/count(*) as total_likes_by_num_of_posts,
		ROUND(COUNT(*) / COUNT(DISTINCT date_trunc('day', cast(created_at as timestamp))), 2) as avg_posts_per_day,
	    ntile(100) OVER (ORDER BY SUM(cast(lf.likes as int))) as likes_percentile,
	    ntile(100) OVER (ORDER BY SUM(cast(lf.replies as int))) as replies_percentile,
		ntile(100) OVER (ORDER BY count(*))	as posts_percentile,
		(ntile(100) OVER (ORDER BY SUM(cast(lf.likes as int))) + ntile(100) OVER (ORDER BY SUM(cast(lf.replies as int))) + ntile(100) OVER (ORDER BY count(*))) / 3.0 as avg_score
	FROM {{ref("latest_feed")}} lf
	GROUP BY REPLACE(author_handle, '"', '') 
),
final as (
	SELECT DISTINCT 
		profiles.handle_subject as profile_handle,
		profiles.profile_did,
		profiles.profile_display_name,
		profiles.profile_avatar,
		profiles.profile_created_date,
		profiles.profile_description,
		user_aggregates.num_posts,
		user_aggregates.average_likes,
		user_aggregates.total_likes,
		user_aggregates.total_replies,
		user_aggregates.total_likes_by_num_of_posts,
		user_aggregates.avg_posts_per_day,
		user_aggregates.likes_percentile,
		user_aggregates.replies_percentile,
		user_aggregates.posts_percentile,
		user_aggregates.avg_score
	FROM profiles
	LEFT JOIN user_aggregates
		ON user_aggregates.author_handle = profiles.handle_subject
)
SELECT * FROM final