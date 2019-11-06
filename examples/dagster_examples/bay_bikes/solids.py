import os
import zipfile
from typing import List

import urllib3

from dagster import solid


def _write_chunks_to_fp(response, output_fp, chunk_size):
    for chunk in response.stream(chunk_size):
        if chunk:
            output_fp.write(chunk)


def _download_zipfile_from_url(url: str, target: str, chunk_size=8192) -> str:
    http = urllib3.PoolManager()
    response = http.request('GET', url, preload_content=False)
    with open(target, 'wb+') as output_fp:
        response.raise_for_status()
        _write_chunks_to_fp(response, output_fp, chunk_size)
    return target


@solid
def download_zipfiles_from_urls(
    _, base_url: str, file_names: List[str], target_dir: str, chunk_size=8192
) -> List[str]:
    for file_name in file_names:
        _download_zipfile_from_url(
            os.path.join(base_url, file_name), os.path.join(target_dir, file_name), chunk_size
        )
    return file_names


def _unzip_file(zipfile_path: str, target: str) -> str:
    with zipfile.ZipFile(zipfile_path, 'r') as zip_fp:
        zip_fp.extractall(target)
    return target


@solid
def unzip_files(_, file_names: List[str], source_dir: str, target_dir: str):
    for file_name in file_names:
        _unzip_file(os.path.join(source_dir, file_name), target_dir)
