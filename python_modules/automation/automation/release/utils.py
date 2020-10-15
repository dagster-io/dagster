import os
import sys
from collections import defaultdict

from automation.git import git_user

if sys.version_info.major >= 3:
    from slack import WebClient  # pylint:disable=import-error
else:
    from slackclient import SlackClient as WebClient  # pylint:disable=import-error


def format_module_versions(module_versions):
    versions = defaultdict(list)

    for module_name, module_version in module_versions.items():
        versions[module_version["__version__"]].append(module_name)

    res = "\n"

    for key, libraries in versions.items():
        res += "%s:\n\t%s\n" % (key, "\n\t".join(libraries))

    return res


def post_to_dagster_slack(checked_version):
    slack_client = WebClient(os.environ["SLACK_RELEASE_BOT_TOKEN"])

    api_params = {
        "channel": "#general",
        "text": ("{git_user} just published a new version: {version}.").format(
            git_user=git_user(), version=checked_version
        ),
    }
    if sys.version_info.major >= 3:
        slack_client.chat_postMessage(**api_params)
    else:
        slack_client.api_call("chat.postMessage", **api_params)
