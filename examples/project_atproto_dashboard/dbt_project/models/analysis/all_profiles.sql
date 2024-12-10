SELECT 
	json_extract_string(json, '$.subject.handle') as handle_subject,
	json_extract_string(json, '$.subject.did') as profile_did,
	json_extract_string(json, '$.subject.avatar') as profile_avatar,
	json_extract_string(json, '$.subject.display_name') as profile_display_name,
	json_extract_string(json, '$.subject.created_at') as profile_created_date,
	json_extract_string(json, '$.subject.description') as profile_description
FROM {{ref("stg_profiles")}}
GROUP BY ALL