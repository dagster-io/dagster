from pathlib import Path

from airflow.models.operator import BaseOperator


def scrape_website(url: str, result_dir: Path) -> None:
    # This is where you would actually scrape the website
    url_to_file = {
        "https://www.customers-data.com": Path(__file__).parent.parent.parent
        / "data"
        / "customers.csv",
    }
    result_file = url_to_file[url]
    # move result file to result_dir
    result_file.rename(result_dir / result_file.name)


class ScraperOperator(BaseOperator):
    def __init__(self, url_to_scrape: str, result_dir: Path, *args, **kwargs):
        self._url_to_scrape = url_to_scrape
        self._result_dir = result_dir
        super().__init__(*args, **kwargs)

    def execute(self, context) -> None:
        # we're not actually going to scrape here, instead we're going to just move files around
        scrape_website(self._url_to_scrape, self._result_dir)
