import json
import os
from dataclasses import dataclass

import dagster as dg
import feedparser
import yagmail
from dagster_aws.s3 import S3Resource
from dagster_modal import ModalClient
from dagster_openai import OpenAIResource

from project_dagster_modal_pipes.constants import DEFAULT_POLLING_INTERVAL, R2_BUCKET_NAME
from project_dagster_modal_pipes.utils import (
    download_bytes,
    file_size,
    get_destination,
    get_entry_audio_url,
    object_exists,
    sanitize,
)
from project_dagster_modal_pipes.utils.summarize import summarize


@dataclass
class RSSFeedDefinition:
    name: str
    url: str
    max_backfill_size: int = 1


def rss_pipeline_factory(feed_definition: RSSFeedDefinition) -> dg.Definitions:
    rss_entry_partition = dg.DynamicPartitionsDefinition(name=f"{feed_definition.name}_entry")

    class AudioRunConfig(dg.Config):
        audio_file_url: str

    audio_asset_name = f"{feed_definition.name}_audio"

    @dg.asset(
        name=audio_asset_name,
        partitions_def=rss_entry_partition,
        compute_kind="python",
    )
    def _podcast_audio(context: dg.AssetExecutionContext, config: AudioRunConfig, s3: S3Resource):
        """Podcast audio file download from RSS feed and uploaded to R2."""
        context.log.info("downloading audio file %s", config.audio_file_url)
        audio_key = get_destination(context.partition_key)

        metadata = {}

        if object_exists(s3.get_client(), bucket=R2_BUCKET_NAME, key=audio_key):
            context.log.info("audio file already exists... skipping")
            metadata["status"] = "cached"
            metadata["key"] = audio_key
        else:
            audio_bytes = download_bytes(config.audio_file_url)
            s3.get_client().put_object(Body=audio_bytes, Bucket=R2_BUCKET_NAME, Key=audio_key)
            metadata["status"] = "uploaded"
            metadata["size"] = file_size(len(audio_bytes))

        return dg.MaterializeResult(metadata=metadata)

    @dg.asset(
        name=f"{feed_definition.name}_transcript",
        partitions_def=rss_entry_partition,
        deps=[_podcast_audio],
        compute_kind="modal",
    )
    def _podcast_transcription(
        context: dg.AssetExecutionContext, modal: ModalClient, s3: S3Resource
    ) -> dg.MaterializeResult:
        """Podcast transcription using OpenAI's Whipser model on Modal."""
        context.log.info("transcript %s", context.partition_key)
        audio_key = get_destination(context.partition_key)
        transcription_key = audio_key.replace(".mp3", ".json")

        if object_exists(s3.get_client(), bucket=R2_BUCKET_NAME, key=transcription_key):
            return dg.MaterializeResult(metadata={"status": "cached"})

        included_env_vars = [
            "CLOUDFLARE_R2_API",
            "CLOUDFLARE_R2_ACCESS_KEY_ID",
            "CLOUDFLARE_R2_SECRET_ACCESS_KEY",
        ]
        env = {k: v for k, v in os.environ.items() if k in included_env_vars}

        return modal.run(
            func_ref="modal_project.transcribe",
            context=context,
            env=env,
            extras={"audio_file_path": audio_key},
        ).get_materialize_result()

    @dg.asset(
        name=f"{feed_definition.name}_summary",
        partitions_def=rss_entry_partition,
        deps=[_podcast_transcription],
        compute_kind="openai",
    )
    def _podcast_summary(
        context: dg.AssetExecutionContext, s3: S3Resource, openai: OpenAIResource
    ) -> dg.MaterializeResult:
        audio_key = get_destination(context.partition_key)
        transcription_key = audio_key.replace(".mp3", ".json")
        summary_key = audio_key.replace(".mp3", "-summary.txt")

        if object_exists(s3.get_client(), bucket=R2_BUCKET_NAME, key=summary_key):
            return dg.MaterializeResult(metadata={"summary": "cached", "summary_key": summary_key})

        response = s3.get_client().get_object(Bucket=R2_BUCKET_NAME, Key=transcription_key)

        data = json.loads(response.get("Body").read())

        with openai.get_client(context) as client:
            summary = summarize(client, data.get("text"))

        s3.get_client().put_object(
            Body=summary.encode("utf-8"), Bucket=R2_BUCKET_NAME, Key=summary_key
        )
        return dg.MaterializeResult(metadata={"summary": summary, "summary_key": summary_key})

    @dg.asset(
        name=f"{feed_definition.name}_email",
        partitions_def=rss_entry_partition,
        deps=[_podcast_summary],
        compute_kind="python",
    )
    def _podcast_email(context: dg.AssetExecutionContext, s3: S3Resource) -> dg.MaterializeResult:
        audio_key = get_destination(context.partition_key)
        summary_key = audio_key.replace(".mp3", "-summary.txt")

        context.log.info("Reading summary %s", summary_key)
        response = s3.get_client().get_object(Bucket=R2_BUCKET_NAME, Key=summary_key)
        summary = response.get("Body").read().decode("utf-8")

        # Expects an application password (see: https://myaccount.google.com/apppasswords)
        yag = yagmail.SMTP(os.environ.get("GMAIL_USER"), os.environ.get("GMAIL_APP_PASSWORD"))

        recipient = os.environ.get("SUMMARY_RECIPIENT_EMAIL")

        yag.send(
            to=recipient,
            subject=f"Podcast Summary: {context.partition_key}",
            contents=f"""
               <h1>Podcast Summary</h1>
               <h2>{context.partition_key}</h2>
               <div>{summary}</div>
            """,
        )

        return dg.MaterializeResult(
            metadata={
                "summary": summary,
                "summary_key": summary_key,
                "recipient": recipient,
            }
        )

    job_name = f"{feed_definition.name}_job"
    _job = dg.define_asset_job(
        name=job_name,
        selection=dg.AssetSelection.assets(
            _podcast_audio, _podcast_transcription, _podcast_summary, _podcast_email
        ),
        partitions_def=rss_entry_partition,
    )

    @dg.sensor(
        name=f"rss_sensor_{feed_definition.name}",
        minimum_interval_seconds=DEFAULT_POLLING_INTERVAL,
        default_status=dg.DefaultSensorStatus.RUNNING,
        job=_job,
    )
    def _sensor(context: dg.SensorEvaluationContext):
        etag = context.cursor
        context.log.info("querying feed with cursor etag: %s", etag)
        feed = feedparser.parse(feed_definition.url, etag=etag)

        num_entries = len(feed.entries)
        context.log.info("total number of entries: %s", num_entries)

        if num_entries > feed_definition.max_backfill_size:
            context.log.info("truncating entries to %s", feed_definition.max_backfill_size)
            entries = feed.entries[: feed_definition.max_backfill_size]
        else:
            entries = feed.entries

        partition_key_audio_files = [
            (sanitize(entry.id), get_entry_audio_url(entry)) for entry in entries
        ]

        return dg.SensorResult(
            run_requests=[
                dg.RunRequest(
                    partition_key=partition_key,
                    run_config=dg.RunConfig(
                        ops={audio_asset_name: AudioRunConfig(audio_file_url=audio_file_url)}
                    ),
                )
                for (partition_key, audio_file_url) in partition_key_audio_files
            ],
            dynamic_partitions_requests=[
                rss_entry_partition.build_add_request(
                    [key for (key, _) in partition_key_audio_files]
                )
            ],
            cursor=feed.etag,
        )

    return dg.Definitions(
        assets=[
            _podcast_audio,
            _podcast_transcription,
            _podcast_summary,
            _podcast_email,
        ],
        jobs=[_job],
        sensors=[_sensor],
    )
