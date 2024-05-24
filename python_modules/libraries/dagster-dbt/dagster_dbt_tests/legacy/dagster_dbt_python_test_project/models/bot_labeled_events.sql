{{ config(tags=["events"]) }}
select blu.is_bot, e.* from
{{ source("dagster", "bot_labeled_users") }} blu join {{ ref("cleaned_events") }} e
on blu.user_id = e.user_id