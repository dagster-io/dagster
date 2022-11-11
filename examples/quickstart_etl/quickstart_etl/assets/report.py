from dagster import MetadataValue, asset


@asset(description="TODO: cloud-friendly outcome, e.g. HTML/image/gist", compute_kind="Plot")
def metrics_report(context, github_stars_by_date, hackernews_stories_by_date):
    df = hackernews_stories_by_date.merge(github_stars_by_date, on="date")

    context.add_output_metadata({"preview": MetadataValue.md(df.head().to_markdown())})
    return df
