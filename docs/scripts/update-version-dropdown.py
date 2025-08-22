"""Update Docusaurus dropdown current version to latest release on GitHub.

USAGE

    $ python scripts/update-version-dropdown.py
    INFO:root:latest version 1.11.7
    INFO:root:current label 1.11.6
    INFO:root:updating docusaurus.config.ts

"""

import json
import logging
import re
import urllib.request

GITHUB_OWNER = "dagster-io"
GITHUB_REPOSITORY = "dagster"
DOCUSAURUS_VERSION_PATTERN = r"label: 'Latest \((\d+.\d+.\d+)\)'"
DOCUSAURUS_CONFIG_PATH = "docusaurus.config.ts"

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPOSITORY}/releases/latest"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode("utf-8"))
        latest_version = data.get("tag_name")

    with open(DOCUSAURUS_CONFIG_PATH) as f:
        content = f.read()

    res = re.search(DOCUSAURUS_VERSION_PATTERN, content)
    current_version = res.group(1)

    logger.info("latest version %s", latest_version)
    logger.info("current label %s", current_version)

    if current_version != latest_version:
        logger.info("updating %s", DOCUSAURUS_CONFIG_PATH)
        updated_docusaurus_config = re.sub(
            DOCUSAURUS_VERSION_PATTERN,
            f"label: 'Latest ({latest_version})'",
            content,
        )
        with open(DOCUSAURUS_CONFIG_PATH, "w") as f:
            f.write(updated_docusaurus_config)
