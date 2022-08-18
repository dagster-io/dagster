"""
A script to verify that every path referred to in a screenshot spec corresponds to a file that
exists in the repo.

Does not ensure that every screenshot referred to in a docs page has an entry in screenshots.yaml
(but that would be a cool thing to add).
"""

import os

import yaml


def match_screenshots():
    with open("./docs/screenshot_capture/screenshots.yaml", "r", encoding="utf8") as f:
        screenshot_specs = yaml.load(f)

    for screenshot_spec in screenshot_specs:
        screenshot_path = os.path.join("docs/next/public/images", screenshot_spec["path"])
        assert os.path.exists(
            screenshot_path
        ), f"Screenshot spec expects a file to exist at {screenshot_path}"

        defs_file = screenshot_spec.get("defs_file")
        if defs_file:
            assert os.path.exists(
                defs_file
            ), f"Screenshot spec expects a file to exist at {defs_file}"


if __name__ == "__main__":
    match_screenshots()
