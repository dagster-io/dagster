With max_profile_data As (
    Select
        json_extract_string(json, '$.subject.did') As profile_did,
        max(
            strptime(
                regexp_extract(
                    filename,
                    'dagster-demo/atproto_starter_pack_snapshot/(\d{4}-\d{2}-\d{2}/\d{2}/\d{2})',
                    1
                ),
                '%Y-%m-%d/%H/%M'
            )
        ) As max_extracted_timestamp
    From {{ ref("stg_profiles") }}
    Group By
        json_extract_string(json, '$.subject.did')
),

profiles As (
    Select
        json_extract_string(json, '$.subject.handle') As handle_subject,
        json_extract_string(json, '$.subject.did') As profile_did,
        json_extract_string(json, '$.subject.avatar') As profile_avatar,
        json_extract_string(json, '$.subject.display_name')
            As profile_display_name,
        json_extract_string(json, '$.subject.created_at')
            As profile_created_date,
        json_extract_string(json, '$.subject.description')
            As profile_description
    From {{ ref("stg_profiles") }} stg_prof
    Join max_profile_data
        On
            json_extract_string(stg_prof.json, '$.subject.did')
            = max_profile_data.profile_did
            And strptime(
                regexp_extract(
                    stg_prof.filename,
                    'dagster-demo/atproto_starter_pack_snapshot/(\d{4}-\d{2}-\d{2}/\d{2}/\d{2})',
                    1
                ),
                '%Y-%m-%d/%H/%M'
            )
            = max_profile_data.max_extracted_timestamp
),

user_aggregates As (
    Select
        replace(author_handle, '"', '') As author_handle,
        count(*) As num_posts,
        avg(cast(lf.likes As int)) As average_likes,
        sum(cast(lf.likes As int)) As total_likes,
        sum(cast(lf.replies As int)) As total_replies,
        sum(cast(lf.likes As int)) / count(*) As total_likes_by_num_of_posts,
        round(
            count(*)
            / count(Distinct date_trunc('day', cast(created_at As timestamp))),
            2
        ) As avg_posts_per_day,
        ntile(100)
            Over (
                Order By sum(cast(lf.likes As int))
            )
            As likes_percentile,
        ntile(100)
            Over (
                Order By sum(cast(lf.replies As int))
            )
            As replies_percentile,
        ntile(100) Over (
            Order By count(*)
        ) As posts_percentile,
        (ntile(100) Over (
            Order By sum(cast(lf.likes As int))) + ntile(100) Over (
            Order By sum(cast(lf.replies As int))) + ntile(100) Over (
            Order By count(*)
        ))
        / 3.0 As avg_score
    From {{ ref("latest_feed") }} lf
    Group By replace(author_handle, '"', '')
),

final As (
    Select Distinct
        profiles.handle_subject As profile_handle,
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
    From profiles
    Left Join user_aggregates
        On user_aggregates.author_handle = profiles.handle_subject
)

Select * From final
