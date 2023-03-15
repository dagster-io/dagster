# ruff: noqa: T201

import glob
import os
import pathlib
import re
import signal
import subprocess
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from time import sleep
from typing import Dict, Optional

from selenium import webdriver  # pylint: disable=import-error
from selenium.webdriver.common.by import By

from dagit_screenshot.defaults import DEFAULT_OUTPUT_ROOT

# Time in seconds that we sleep waiting for a dagit route to load
DAGIT_ROUTE_LOAD_TIME = 2

# Time in seconds that we sleep waiting for the dagit process to start up
DAGIT_STARTUP_TIME = 6

# Time in seconds we sleep to wait for Dagit to finish downloading the SVG
DOWNLOAD_SVG_TIME = 2

SVG_ROOT = os.path.join(DEFAULT_OUTPUT_ROOT, "asset-screenshots")

CODE_SAMPLES_ROOT = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "..",
    "examples",
    "docs_snippets",
    "docs_snippets",
)

SVG_FONT_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "static", "font_info.svg")

with open(SVG_FONT_DATA_FILE, "r", encoding="utf-8") as f:
    SVG_FONT_DATA = f.read()


def _add_font_info_to_svg(svg_filepath: str):
    """Adds embedded Dagster font information to an SVG file downloaded from Dagit."""
    with open(svg_filepath, "r", encoding="utf-8") as f:
        svg = f.read()
    with open(svg_filepath, "w", encoding="utf-8") as f:
        f.write(svg.replace('<style xmlns="http://www.w3.org/1999/xhtml"></style>', SVG_FONT_DATA))


def _get_latest_download(file_extension: str) -> str:
    """Returns the path to the most recently downloaded file with the given extension."""
    # https://stackoverflow.com/a/60004701
    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
    list_of_downloads = glob.glob(downloads_folder + f"/*.{file_extension}")
    return max(list_of_downloads, key=os.path.getctime)


@contextmanager
def _setup_snippet_file(code_path: str, snippet_fn: Optional[str]):
    """Creates a temporary file that contains the contents of the given code file,
    setting up the given snippet function as a repository if specified.
    """
    with TemporaryDirectory() as temp_dir:
        with open(code_path, "r", encoding="utf-8") as f:
            code = f.read()

        if snippet_fn:
            code = f"""{code}

from dagster import repository
@repository
def demo_repo():
    return {snippet_fn}()
"""

        temp_code_file = os.path.join(temp_dir, "code.py")
        with open(temp_code_file, "w", encoding="utf-8") as f:
            f.write(code)
        yield temp_code_file


def generate_svg_for_file(code_path: str, destination_path: str, snippet_fn: Optional[str]):
    """Generates an SVG for the given code file & entry function, saving it to the given destination path.
    """
    driver = None
    dagit_process = None

    try:
        with _setup_snippet_file(code_path, snippet_fn) as temp_code_file:
            command = ["dagit", "-f", temp_code_file]

            dagit_process = subprocess.Popen(command)
            sleep(DAGIT_STARTUP_TIME)  # Wait for the dagit server to start up

            driver = webdriver.Chrome()
            driver.set_window_size(1024, 768)
            driver.get("http://localhost:3000")
            driver.execute_script("window.localStorage.setItem('communityNux','1')")
            driver.refresh()

            sleep(DAGIT_ROUTE_LOAD_TIME)  # wait for page to load

            element = driver.find_element(By.XPATH, '//div[@aria-label="download_for_offline"]')
            element.click()

            sleep(DOWNLOAD_SVG_TIME)  # wait for download to complete

            downloaded_file = _get_latest_download("svg")
            pathlib.Path(destination_path).parent.mkdir(parents=True, exist_ok=True)
            output_file = destination_path
            os.rename(downloaded_file, output_file)

            _add_font_info_to_svg(output_file)

    finally:
        if driver:  # quit chrome
            driver.quit()
        if dagit_process:  # quit dagit
            dagit_process.send_signal(signal.SIGINT)
            dagit_process.wait()


def parse_params(param_str: str) -> Dict[str, str]:
    """Parses a set of params for a markdown code block.

    For example, returns {"foo": "bar", "baz": "qux"} for:

    ```python
    foo=bar baz=qux.
    ```
    """
    params = re.split(r"\s+", param_str)
    return {param.split("=")[0]: param.split("=")[1] for param in params if len(param) > 0}


def generate_svg(target_mdx_file: str):
    # Parse all code blocks in the MD file
    with open(target_mdx_file, "r", encoding="utf-8") as f:
        snippets = [
            parse_params(x) for x in re.findall(r"```python([^\n]+dagimage[^\n]+)", f.read())
        ]

    updated_snippet_params = []
    for snippet_params in snippets:
        filepath = snippet_params["file"]
        snippet_fn = snippet_params.get("function")

        destination_file_path = f".{filepath[:-3]}{'/' + snippet_fn if snippet_fn else ''}.svg"
        generate_svg_for_file(
            os.path.join(CODE_SAMPLES_ROOT, f".{filepath}"),
            os.path.join(SVG_ROOT, destination_file_path),
            snippet_fn,
        )
        # Add pointer to the generated screenshot to the params for the code block
        updated_snippet_params.append(
            {
                **snippet_params,
                "dagimage": os.path.normpath(
                    os.path.join("images", "asset-screenshots", destination_file_path)
                ),
            }
        )

    with open(target_mdx_file, "r", encoding="utf-8") as f:
        pattern = re.compile(r"(```python)([^\n]+dagimage[^\n]+)", re.S)

        # Find and replace the code block params with our updated params
        # https://stackoverflow.com/a/16762053
        idx = [0]

        def _replace(match):
            snippet_parmas = updated_snippet_params[idx[0]]
            snippet_params_text = " ".join(f"{k}={v}" for k, v in snippet_parmas.items())
            out = f"{match.group(1)} {snippet_params_text}"
            idx[0] += 1
            return out

        updated_mdx_contents = re.sub(
            pattern,
            _replace,
            f.read(),
        )

    with open(target_mdx_file, "w", encoding="utf-8") as f:
        f.write(updated_mdx_contents)
