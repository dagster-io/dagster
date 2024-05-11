import modal  # type: ignore

app = modal.App("schrockn-project-pipes-kicktest")

slack_sdk_image = modal.Image.debian_slim().pip_install("slack-sdk")
# secrets = [modal.Secret.from_name("modal-test-chat-write")]
secrets = []


@app.function(image=slack_sdk_image, secrets=secrets)
def asset_two_on_modal() -> dict:
    # import slack_sdk  # type: ignore

    # client = slack_sdk.WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    # response = client.chat_postMessage(
    #     channel="modal-test-channel", text="hello world from modal on aws."
    # )
    # return {
    #     "metadata_from_cloud": "blah_updated",
    #     "response": {"type": "json", "raw_value": response.data},
    # }
    return {
        "metadata_from_cloud": "blah_updated",
        "response": {"type": "json", "raw_value": {"imagine": "realities"}},
    }


@app.local_entrypoint()
def main() -> None:
    from dagster_pipes import open_dagster_pipes

    with open_dagster_pipes() as pipes:
        pipes.log.info("This code is running on local.")
        metadata_returned = asset_two_on_modal.remote()
        pipes.report_asset_materialization(metadata_returned)


if __name__ == "__main__":
    ...
