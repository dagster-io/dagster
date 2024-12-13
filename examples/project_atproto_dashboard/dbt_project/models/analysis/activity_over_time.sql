With final As (
    Select
        date_trunc('day', created_at) As post_date,
        count(Distinct post_text) As unique_posts,
        count(Distinct author_handle) As active_authors,
        sum(likes) As total_likes,
        sum(replies) As total_comments,
        sum(quotes) As total_quotes
    From {{ ref("latest_feed") }}
    Group By date_trunc('day', created_at)
    Order By date_trunc('day', created_at) Desc
)

Select * From final
