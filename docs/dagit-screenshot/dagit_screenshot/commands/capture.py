# pylint: disable=print-call

import os
import signal
import subprocess
from time import sleep
from dagit_screenshot.utils import ScreenshotSpec

from selenium import webdriver  # pylint: disable=import-error
from typing_extensions import NotRequired, TypeAlias, TypedDict

# Time in seconds that we sleep waiting for a dagit route to load
DAGIT_ROUTE_LOAD_TIME = 1

# Time in seconds that we sleep waiting for the dagit process to start up
DAGIT_STARTUP_TIME = 6

# Browser window size for a given screenshot is set by the screenshot size with width and height
# scaled by this factor. Note that this only affects the displayed browser window size, not the size
# of the saved screenshot image file.
WINDOW_SCALE_FACTOR = 1.3


def capture(spec: ScreenshotSpec, output_path: str) -> None:
    dagit_process = None

    try:
        assert "workspace" in spec, 'spec must define a "workspace"'
        workspace = spec["workspace"]
        if workspace.endswith(".py"):
            command = ["dagit", "-f", workspace]
        elif workspace.endswith(".yaml"):
            command = ["dagit", "-w", workspace]
        else:
            raise Exception("'workspace' must be a .py or .yaml file.")

        print("Starting dagit:")
        print("  " + " ".join(command))
        dagit_process = subprocess.Popen(command)
        sleep(DAGIT_STARTUP_TIME)  # Wait for the dagit server to start up

        driver = webdriver.Chrome()
        driver.set_window_size(
            spec.get("width", 1024 * WINDOW_SCALE_FACTOR),
            spec.get("height", 768 * WINDOW_SCALE_FACTOR),
        )
        driver.get(spec["route"])
        sleep(DAGIT_ROUTE_LOAD_TIME)  # wait for page to load

        if "steps" in spec:
            print("Perform these steps to prepare dagit for screenshot capture:")
            for step in spec["steps"]:
                print(f"- {step}")
            input("Press Enter to capture...")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        driver.get_screenshot_as_file(output_path)
        print(f"Saved screenshot to {output_path}")
        driver.quit()
    finally:
        if dagit_process:  # quit dagit
            dagit_process.send_signal(signal.SIGINT)
            dagit_process.wait()
