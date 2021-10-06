from hacker_news_assets.pipelines.dbt_pipeline import activity_stats


def test_activity_forecast():
    result = activity_stats.execute_in_process()
    assert result.success
