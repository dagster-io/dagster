"""Transcribe podcasts using OpenAI's Whisper model on Modal.

Example Usage

    modal run modal_project.transcribe

"""

import json
import os
import pathlib
from collections.abc import Iterator
from pathlib import Path
from typing import TypedDict

import modal

from . import config


class Segment(TypedDict):
    text: str
    start: float
    end: float


logger = config.get_logger(__name__)


def coalesce_short_transcript_segments(
    segments: list[Segment],
) -> list[Segment]:
    minimum_transcript_len = 200  # About 2 sentences.
    previous = None
    long_enough_segments = []
    for current in segments:
        if previous is None:
            previous = current
        elif len(previous["text"]) < minimum_transcript_len:
            previous = _merge_segments(left=previous, right=current)
        else:
            long_enough_segments.append(previous)
            previous = current
    if previous:
        long_enough_segments.append(previous)
    return long_enough_segments


def _merge_segments(left: Segment, right: Segment) -> Segment:
    return {
        "text": left["text"] + " " + right["text"],
        "start": left["start"],
        "end": right["end"],
    }


app_image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("git")
    .pip_install(
        "git+https://github.com/openai/whisper.git",
        "dacite",
        "jiwer",
        "ffmpeg-python",
        "gql[all]~=3.0.0a5",
        "python-multipart~=0.0.9",
        "pandas",
        "loguru==0.6.0",
        "torchaudio==2.1.0",
        "python-dotenv",
    )
    .apt_install("ffmpeg")
    .pip_install("ffmpeg-python")
)

app = modal.App(
    "whisper-pod-transcriber",
    image=app_image,
)

cloud_bucket_mount = modal.CloudBucketMount(
    "dagster-modal-demo",
    bucket_endpoint_url=os.environ.get("CLOUDFLARE_R2_API"),
    secret=modal.Secret.from_dict(
        {
            "AWS_ACCESS_KEY_ID": os.environ.get("CLOUDFLARE_R2_ACCESS_KEY_ID"),
            "AWS_SECRET_ACCESS_KEY": os.environ.get("CLOUDFLARE_R2_SECRET_ACCESS_KEY"),
            "AWS_REGION": "auto",
        }
    ),
)


def split_silences(
    path: str, min_segment_length: float = 30.0, min_silence_length: float = 1.0
) -> Iterator[tuple[float, float]]:
    """Split audio file into contiguous chunks using the ffmpeg `silencedetect` filter.

    Retuns:
        Generator of tuples (start, end) of each chunk in seconds.

    """
    import re

    import ffmpeg

    silence_end_re = re.compile(
        r" silence_end: (?P<end>[0-9]+(\.?[0-9]*)) \| silence_duration: (?P<dur>[0-9]+(\.?[0-9]*))"
    )

    metadata = ffmpeg.probe(path)
    duration = float(metadata["format"]["duration"])

    reader = (
        ffmpeg.input(str(path))
        .filter("silencedetect", n="-10dB", d=min_silence_length)
        .output("pipe:", format="null")
        .run_async(pipe_stderr=True)
    )

    cur_start = 0.0
    num_segments = 0

    while True:
        line = reader.stderr.readline().decode("utf-8")
        if not line:
            break
        match = silence_end_re.search(line)
        if match:
            silence_end, silence_dur = match.group("end"), match.group("dur")
            split_at = float(silence_end) - (float(silence_dur) / 2)

            if (split_at - cur_start) < min_segment_length:
                continue

            yield cur_start, split_at
            cur_start = split_at
            num_segments += 1

    # silencedetect can place the silence end *after* the end of the full audio segment.
    # Such segments definitions are negative length and invalid.
    if duration > cur_start:
        yield cur_start, duration
        num_segments += 1
    logger.info(f"Split {path} into {num_segments} segments")


@app.function(
    image=app_image,
    cpu=2,
    timeout=400,
    volumes={
        "/mount": cloud_bucket_mount,
    },
)
def transcribe_segment(
    start: float,
    end: float,
    audio_filepath: pathlib.Path,
    model: config.ModelSpec,
):
    import tempfile
    import time

    import ffmpeg
    import torch
    import whisper  # type: ignore

    t0 = time.time()
    with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
        (
            ffmpeg.input(str(audio_filepath))
            .filter("atrim", start=start, end=end)
            .output(f.name)
            .overwrite_output()
            .run(quiet=True)
        )

        use_gpu = torch.cuda.is_available()
        device = "cuda" if use_gpu else "cpu"
        model = whisper.load_model(model.name, device=device, download_root=config.MODEL_DIR)
        result = model.transcribe(f.name, language="en", fp16=use_gpu)  # type: ignore

    logger.info(
        f"Transcribed segment {start:.2f} to {end:.2f} ({end - start:.2f}s duration) in {time.time() - t0:.2f} seconds."
    )

    # Add back offsets.
    for segment in result["segments"]:
        segment["start"] += start
        segment["end"] += start

    return result


@app.function(
    image=app_image,
    timeout=900,
    volumes={
        "/mount": cloud_bucket_mount,
    },
)
def transcribe_episode(
    audio_file: pathlib.Path,
    result_path: pathlib.Path,
    model: config.ModelSpec,
    force: bool = False,
):
    if not audio_file.exists():
        raise Exception("Audio file not present on the file system")

    if os.path.exists(result_path) and not force:
        logger.info("Transcript already exists, skipping...")
        return

    segment_gen = split_silences(str(audio_file))

    output_text = ""
    output_segments = []
    for result in transcribe_segment.starmap(
        segment_gen, kwargs=dict(audio_filepath=audio_file, model=model)
    ):
        output_text += result["text"]
        output_segments += result["segments"]

    result = {
        "text": output_text,
        "segments": output_segments,
        "language": "en",
    }

    logger.info(f"Writing openai/whisper transcription to {result_path}")
    with open(result_path, "w") as f:
        json.dump(result, f, indent=4)


@app.local_entrypoint()
def main():
    from dagster_pipes import open_dagster_pipes

    model = config.DEFAULT_MODEL

    with open_dagster_pipes() as context:
        audio_path = context.extras.get("audio_file_path")
        if not audio_path:
            raise Exception("Missing `audio_file_path` extras parameter")

        audio_path = "/mount/" + audio_path
        transcription_path = audio_path.replace(".mp3", ".json")
        transcribe_episode.remote(
            audio_file=Path(audio_path),
            result_path=Path(transcription_path),
            model=model,
        )

        context.report_asset_materialization(
            metadata={
                "audio_file": audio_path,
                "transcription_file": transcription_path,
            }
        )
