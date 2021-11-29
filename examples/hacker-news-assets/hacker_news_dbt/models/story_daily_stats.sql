SELECT date_trunc("day", to_timestamp("time")) as date,
       count(DISTINCT "by") AS posting_users,
       count(*) AS num_stories
FROM {{ source('hackernews', 'stories') }}
GROUP BY 1
