import json
import os
import urllib.request
import zipfile

import pendulum
import requests
from dagster import DynamicPartitionsDefinition, Output, asset, get_dagster_logger
from pandas import DataFrame

releases_partitions_def = DynamicPartitionsDefinition(name="releases")


@asset(
    partitions_def=releases_partitions_def,
    io_manager_key="warehouse",
    metadata={"partition_expr": "release_tag"},
)
def releases_metadata(context) -> DataFrame:
    """Table with a single row per release."""
    release_tag = context.partition_key

    response = requests.get(
        f"https://api.github.com/repos/dagster-io/dagster/releases/tags/{release_tag}",
        auth=(os.environ["GITHUB_USER_NAME"], os.environ["GITHUB_ACCESS_TOKEN"]),
    )
    if not response.ok:
        response.raise_for_status()

    response_content = json.loads(response.content)

    return DataFrame(
        [
            {
                "release_tag": release_tag,
                "tarball_url": response_content["tarball_url"],
                "zipball_url": response_content["zipball_url"],
                "id": response_content["id"],
                "author_login": response_content["author"]["login"],
                "published_at": pendulum.parse(response_content["published_at"]),
            }
        ]
    )


def _get_release_zip_path(release_tag: str) -> str:
    return f"data/releases/{release_tag}.zip"


@asset(partitions_def=releases_partitions_def)
def release_zips(context, releases_metadata: DataFrame) -> None:
    """Directory containing a zip file for each release."""
    zipball_url = releases_metadata.iloc[0]["zipball_url"]

    target_zip_path = _get_release_zip_path(context.partition_key)
    os.mkdir(os.path.dirname(target_zip_path))
    urllib.request.urlretrieve(zipball_url, target_zip_path)


def _get_release_files_dir(release_tag: str) -> str:
    return f"data/releases/{release_tag}/"


@asset(partitions_def=releases_partitions_def, non_argument_deps={"release_zips"})
def release_files(context) -> None:
    """Directory with a subdirectory for each release."""
    release_files_dir = _get_release_files_dir(context.partition_key)
    os.mkdir(release_files_dir)
    with zipfile.ZipFile(_get_release_zip_path(context.partition_key), "r") as zip_ref:
        zip_ref.extractall(release_files_dir)


@asset(
    partitions_def=releases_partitions_def,
    non_argument_deps={"release_files"},
    io_manager_key="warehouse",
    metadata={"partition_expr": "release_tag"},
)
def release_files_metadata(context) -> DataFrame:
    """
    Table with a row for every release file.

    Partitioned by release, because all the files for a release are added/updated atomically
    """
    file_metadata = []

    release_files_dir = _get_release_files_dir(context.partition_key)
    get_dagster_logger().info(f"release_files_dir: {release_files_dir}")

    for path, dirs, files in os.walk(release_files_dir):
        for f in files:
            file_path = os.path.join(path, f)
            file_metadata.append(
                {
                    "release_tag": context.partition_key,
                    "path": os.path.relpath(file_path, release_files_dir),
                    "size_bytes": os.path.getsize(file_path),
                }
            )

    return DataFrame(file_metadata)


@asset(io_manager_key="warehouse")
def releases_summary(
    releases_metadata: DataFrame, release_files_metadata: DataFrame
) -> Output[DataFrame]:
    release_sizes = release_files_metadata.groupby("release_tag")["size_bytes"].sum()
    biggest_release_tag = release_sizes.idxmax()
    biggest_release_metadata = releases_metadata[
        releases_metadata["release_tag"] == biggest_release_tag
    ].iloc[0]

    df = DataFrame(
        [
            {
                "releases_total_size": release_sizes.sum(),
                "biggest_release_tag": biggest_release_tag,
                "biggest_release_size": release_sizes[biggest_release_tag],
                "biggest_release_published_at": biggest_release_metadata["published_at"],
                "biggest_release_author_login": biggest_release_metadata["author_login"],
            }
        ]
    )
    return Output(df, metadata={"preview": df.to_markdown()})
