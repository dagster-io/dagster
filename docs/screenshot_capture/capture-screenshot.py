# pylint: disable=print-call
"""
Captures a screenshot, based on a screenshot spec.

Meant to be called from the repo root.

Usage example:
    python docs/screenshot_capture/capture_screenshot.py concepts/dagit/runs-tab.png
"""

import os
import signal
import subprocess
import sys
from time import sleep
from typing import Mapping, Sequence

import yaml
from selenium import webdriver


def load_screenshot_specs():
    with open("./docs/screenshot_capture/screenshots.yaml", "r") as f:
        return yaml.load(f)


def capture_screenshots(screenshot_specs: Sequence[Mapping[str, str]]):
    for screenshot_spec in screenshot_specs:
        dagit_process = None
        try:
            defs_file = screenshot_spec.get("defs_file")
            if defs_file:
                if defs_file.endswith(".py"):
                    command = ["dagit", "-f", defs_file]
                elif defs_file.endswith(".yaml"):
                    command = ["dagit", "-w", defs_file]
                else:
                    assert False, "defs_file must be .py or .yaml"

                print("Running this command:")
                print(" ".join(command))
                dagit_process = subprocess.Popen(command)
                sleep(6)

            driver = webdriver.Chrome()
            driver.set_window_size(
                screenshot_spec.get("width", 1024 * 1.3), screenshot_spec.get("height", 768 * 1.3)
            )
            driver.get(screenshot_spec["url"])
            sleep(1)

            if "steps" in screenshot_spec:
                for step in screenshot_spec["steps"]:
                    print(step)
                input("Press Enter to continue...")

            screenshot_path = os.path.join("docs/next/public/images", screenshot_spec["path"])
            driver.get_screenshot_as_file(screenshot_path)
            print(f"Saved screenshot to {screenshot_path}")
            driver.quit()
        finally:
            if dagit_process:
                dagit_process.send_signal(signal.SIGINT)
                dagit_process.wait()


def main():
    screenshot_specs = load_screenshot_specs()

    assert len(sys.argv) > 1
    screenshot_name = sys.argv[1]
    matching_specs = [spec for spec in screenshot_specs if spec["path"] == screenshot_name]
    if len(matching_specs) > 1:
        print("Multiple matching screenshot paths")
        sys.exit(1)

    if len(matching_specs) == 0:
        print("No matching screenshot paths")
        sys.exit(1)

    capture_screenshots(matching_specs)


if __name__ == "__main__":
    main()
