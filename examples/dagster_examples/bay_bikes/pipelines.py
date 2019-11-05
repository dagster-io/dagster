from dagster import pipeline

from .solids import download_zipfiles_from_urls, unzip_files


@pipeline
def download_csv_pipeline():
    file_names = download_zipfiles_from_urls()
    unzip_files(file_names)
