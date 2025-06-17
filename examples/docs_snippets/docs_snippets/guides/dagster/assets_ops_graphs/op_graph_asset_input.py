import dagster as dg


@dg.asset
def emails_to_send(): ...


@dg.op
def send_emails(emails) -> None: ...


@dg.job
def send_emails_job():
    send_emails(emails_to_send.get_asset_spec())
