from dagster import asset, job, op


@asset
def emails_to_send(): ...


@op
def send_emails(emails) -> None: ...


@job
def send_emails_job():
    send_emails(emails_to_send.get_asset_spec())
