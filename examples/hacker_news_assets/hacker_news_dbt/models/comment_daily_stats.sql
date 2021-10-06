SELECT date_trunc("day", to_timestamp("time")) as date,
       count(DISTINCT "by") AS commenting_users,
       count(*) AS num_comments
FROM {{ source('hackernews', 'comments') }}
GROUP BY 1
