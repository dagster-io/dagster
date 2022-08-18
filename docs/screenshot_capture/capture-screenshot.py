# pylint: disable=print-call
"""
Captures a screenshot, based on a screenshot spec.

Meant to be called from the repo root.

Usage example:
    python docs/screenshot_capture/capture-screenshot.py concepts/dagit/runs-tab.png
"""

import os
import signal
import subprocess
import sys
from time import sleep
from typing import Any, List, Mapping, Sequence

import yaml
from selenium import webdriver  # pylint: disable=import-error
from typing_extensions import NotRequired, TypedDict


class ScreenshotSpec(TypedDict):
    path: str
    defs_file: str
    url: str
    steps: NotRequired[List[str]]
    vetted: NotRequired[bool]
    width: NotRequired[int]
    height: NotRequired[int]


def load_screenshot_specs(path) -> Sequence[Mapping]:
    with open(path, "r", encoding="utf8") as f:
        return yaml.safe_load(f)


WINDOW_SCALE_FACTOR = 1.3

def capture_screenshot(screenshot_spec: Mapping[str, str], save_path: str) -> None:
    dagit_process = None
    try:
        defs_file = screenshot_spec.get("defs_file")
        if defs_file:
            if defs_file.endswith(".py"):
                command = ["dagit", "-f", defs_file]
            elif defs_file.endswith(".yaml"):
                command = ["dagit", "-w", defs_file]
            else:
                raise Exception("defs_file must be .py or .yaml")

            print("Running this command:")
            print(" ".join(command))
            dagit_process = subprocess.Popen(command)
            sleep(6)  # Wait for the dagit server to start up

        driver = webdriver.Chrome()
        driver.set_window_size(
            screenshot_spec.get("width", 1024 * WINDOW_SCALE_FACTOR), screenshot_spec.get("height", 768 * WINDOW_SCALE_FACTOR)
        )
        driver.get(screenshot_spec["url"])
        sleep(1)  # wait for page to load

        if "steps" in screenshot_spec:
            for step in screenshot_spec["steps"]:
                print(step)
            input("Press Enter to continue...")

        full_save_path = os.path.join("docs/next/public/images", save_path)
        os.makedirs(os.path.dirname(full_save_path), exist_ok=True)
        driver.get_screenshot_as_file(full_save_path)
        print(f"Saved screenshot to {full_save_path}")
        driver.quit()
    finally:
        if dagit_process:
            dagit_process.send_signal(signal.SIGINT)
            dagit_process.wait()


def find_screenshot_spec(screenshot_path: str) -> Mapping[str, Any]:
    components = screenshot_path.split("/")
    screenshot_specs_file_path = (
        os.path.join(".", "docs", "screenshot_capture", *components[:-1]) + ".yaml"
    )
    screenshot_name = components[-1]
    if os.path.exists(screenshot_specs_file_path):
        screenshot_specs = load_screenshot_specs(screenshot_specs_file_path)
        matching_specs = [spec for spec in screenshot_specs if spec["path"] == screenshot_name]
    else:
        print(f"{screenshot_specs_file_path} does not exist. Looking in mega screenshots.yaml.")
        screenshot_specs = load_screenshot_specs("./docs/screenshot_capture/screenshots.yaml")
        matching_specs = [spec for spec in screenshot_specs if spec["path"] == screenshot_path]

    if len(matching_specs) > 1:
        print("Multiple matching screenshot paths")
        sys.exit(1)

    if len(matching_specs) == 0:
        print("No matching screenshot paths")
        sys.exit(1)

    return matching_specs[0]


def main():
    assert len(sys.argv) > 1
    screenshot_path = sys.argv[1]
    screenshot_spec = find_screenshot_spec(screenshot_path)
    capture_screenshot(screenshot_spec, screenshot_path)


if __name__ == "__main__":
    main()
