WITH max_profile_data AS (
    SELECT
        json_extract_string(json, '$.subject.did') AS profile_did,
        max(
            strptime(
                regexp_extract(
                    filename,
                    'dagster-demo/atproto_starter_pack_snapshot/(\d{4}-\d{2}-\d{2}/\d{2}/\d{2})',
                    1
                ),
                '%Y-%m-%d/%H/%M'
            )
        ) AS max_extracted_timestamp
    FROM {{ ref("stg_profiles") }}
    GROUP BY
        json_extract_string(json, '$.subject.did')
),

profiles AS (
    SELECT
        json_extract_string(json, '$.subject.handle') AS handle_subject,
        json_extract_string(json, '$.subject.did') AS profile_did,
        json_extract_string(json, '$.subject.avatar') AS profile_avatar,
        json_extract_string(json, '$.subject.display_name')
            AS profile_display_name,
        json_extract_string(json, '$.subject.created_at')
            AS profile_created_date,
        json_extract_string(json, '$.subject.description')
            AS profile_description
    FROM {{ ref("stg_profiles") }} stg_prof
    JOIN max_profile_data
        ON
            json_extract_string(stg_prof.json, '$.subject.did')
            = max_profile_data.profile_did
            AND strptime(
                regexp_extract(
                    stg_prof.filename,
                    'dagster-demo/atproto_starter_pack_snapshot/(\d{4}-\d{2}-\d{2}/\d{2}/\d{2})',
                    1
                ),
                '%Y-%m-%d/%H/%M'
            )
            = max_profile_data.max_extracted_timestamp
),

user_aggregates AS (
    SELECT
        replace(author_handle, '"', '') AS author_handle,
        count(*) AS num_posts,
        avg(cast(lf.likes AS int)) AS average_likes,
        sum(cast(lf.likes AS int)) AS total_likes,
        sum(cast(lf.replies AS int)) AS total_replies,
        sum(cast(lf.likes AS int)) / count(*) AS total_likes_by_num_of_posts,
        round(
            count(*)
            / count(DISTINCT date_trunc('day', cast(created_at AS timestamp))),
            2
        ) AS avg_posts_per_day,
        ntile(100)
            OVER (
                ORDER BY sum(cast(lf.likes AS int))
            )
            AS likes_percentile,
        ntile(100)
            OVER (
                ORDER BY sum(cast(lf.replies AS int))
            )
            AS replies_percentile,
        ntile(100) OVER (
            ORDER BY count(*)
        ) AS posts_percentile,
        (ntile(100) OVER (
            ORDER BY sum(cast(lf.likes AS int))) + ntile(100) OVER (
            ORDER BY sum(cast(lf.replies AS int))) + ntile(100) OVER (
            ORDER BY count(*)
        ))
        / 3.0 AS avg_score
    FROM {{ ref("latest_feed") }} lf
    GROUP BY replace(author_handle, '"', '')
),

final AS (
    SELECT DISTINCT
        profiles.handle_subject AS profile_handle,
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
