SELECT date_trunc('day', to_timestamp(time::int)) as date,
       count(DISTINCT user_id) AS commenting_users,
       count(*) AS num_comments
FROM {{ source('hackernews', 'comments') }}
GROUP BY 1
