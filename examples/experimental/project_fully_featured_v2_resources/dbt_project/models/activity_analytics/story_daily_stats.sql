SELECT date_trunc('day', to_timestamp(time::int)) as date,
       count(DISTINCT user_id) AS posting_users,
       count(*) AS num_stories
FROM {{ source('hackernews', 'stories') }}
GROUP BY 1
