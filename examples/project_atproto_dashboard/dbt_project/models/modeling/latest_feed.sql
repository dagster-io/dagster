WITH max_update AS (
    SELECT
        max(
            strptime(
                regexp_extract(
                    filename,
                    'dagster-demo/atproto_actor_feed_snapshot/(\d{4}-\d{2}-\d{2}/\d{2}/\d{2})',
                    1
                ),
                '%Y-%m-%d/%H/%M'
            )
        ) AS max_extracted_timestamp,
        regexp_extract(filename, 'did:(.*?)\.json') AS profile_id
    FROM {{ ref("stg_feed_snapshots") }}
    GROUP BY
        regexp_extract(filename, 'did:(.*?)\.json')
),

final AS (
    SELECT
        json_extract_string(sfs.json, '$.post.author.handle') AS author_handle,
        json_extract_string(sfs.json, '$.post.author.did') AS author_id,
        cast(sfs.json.post.like_count AS int) AS likes,
        cast(sfs.json.post.quote_count AS int) AS quotes,
        cast(sfs.json.post.reply_count AS int) AS replies,
        json_extract_string(sfs.json, '$.post.record.text') AS post_text,
        sfs.json.post.record.embed,
        json_extract_string(
            sfs.json, '$.post.record.embed.external.description'
        ) AS external_embed_description,
        json_extract_string(sfs.json, '$.post.record.embed.external.uri')
            AS external_embed_link,
        sfs.json.post.record.embed.external.thumb AS external_embed_thumbnail,
        cast(sfs.json.post.record.created_at AS timestamp) AS created_at,
        CASE 
	        WHEN json_extract_string(sfs.json.post.record.embed, '$.images[0].image.ref.link') IS NULL THEN NULL
            ELSE concat('https://cdn.bsky.app/img/feed_thumbnail/plain/', json_extract_string(sfs.json, '$.post.author.did') ,'/' ,json_extract_string(sfs.json.post.record.embed, '$.images[0].image.ref.link'), '@jpeg')
        END AS image_url,
        max_update.max_extracted_timestamp,
        max_update.profile_id
    FROM {{ ref("stg_feed_snapshots") }} sfs
    JOIN max_update
        ON
            max_update.profile_id
            = regexp_extract(sfs.filename, 'did:(.*?)\.json')
            AND max_update.max_extracted_timestamp
            = strptime(
                regexp_extract(
                    sfs.filename,
                    'dagster-demo/atproto_actor_feed_snapshot/(\d{4}-\d{2}-\d{2}/\d{2}/\d{2})',
                    1
                ),
                '%Y-%m-%d/%H/%M'
            )
)

SELECT * FROM final
