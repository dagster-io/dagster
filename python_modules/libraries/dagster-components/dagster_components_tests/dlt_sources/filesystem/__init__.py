from typing import Any, Iterator, List, Tuple

import dlt
from dlt.sources import DltResource, TDataItems
from dlt.sources.filesystem import FileItem, FileItemDict, fsspec_filesystem, glob_files


def _read_csv(
    items: Iterator[FileItemDict], chunksize: int = 10000, **pandas_kwargs: Any
) -> Iterator[TDataItems]:
    import pandas as pd

    kwargs = {**{"header": "infer", "chunksize": chunksize}, **pandas_kwargs}
    for file_obj in items:
        with file_obj.open() as file:
            for df in pd.read_csv(file, **kwargs):
                yield df.to_dict(orient="records")


@dlt.resource(primary_key="file_url", standalone=True)
def filesystem(
    bucket_url: str = dlt.secrets.value,
    file_glob: str = "*",
    files_per_page: int = 100,
    extract_content: bool = False,
) -> Iterator[List[FileItem]]:
    fs_client = fsspec_filesystem(bucket_url)[0]

    files_chunk: List[FileItem] = []
    for file_model in glob_files(fs_client, bucket_url, file_glob):
        file_dict = FileItemDict(file_model)
        if extract_content:
            file_dict["file_content"] = file_dict.read_bytes()
        files_chunk.append(file_dict)  # type: ignore

        # wait for the chunk to be full
        if len(files_chunk) >= files_per_page:
            yield files_chunk
            files_chunk = []
    if files_chunk:
        yield files_chunk


@dlt.source()
def csv_source(
    bucket_url: str = dlt.secrets.value, file_glob: str = "*"
) -> Tuple[DltResource, ...]:
    return (
        filesystem(bucket_url, file_glob=file_glob) | dlt.transformer(name="read_csv")(_read_csv),
    )
