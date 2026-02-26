import logging
import time
from dataclasses import dataclass
from functools import lru_cache

import requests
from buildkite_shared.context import BuildkiteContext


@dataclass(frozen=True)
class QuarantinedObject:
    scope: str
    name: str
    web_url: str

    def __eq__(self, other):
        return self.scope == other.scope and self.name == other.name

    def __hash__(self):
        return hash((self.scope, self.name))


@lru_cache
def get_buildkite_quarantined_objects(
    token, org_slug, suite_slug, annotation, suppress_errors=False
) -> set[QuarantinedObject]:
    quarantined_objects = set()
    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://api.buildkite.com/v2/analytics/organizations/{org_slug}/suites/{suite_slug}/tests/{annotation}"

        start_time = time.time()
        timeout = 10

        while url and time.time() - start_time < timeout:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            for test in response.json():
                scope = test.get("scope", "")
                name = " ".join(test.get("name", "").split())
                web_url = test.get("web_url", "")
                quarantined_object = QuarantinedObject(scope, name, web_url)
                quarantined_objects.add(quarantined_object)

            link_header = response.headers.get("Link", "")
            next_url = None
            for part in link_header.split(","):
                if 'rel="next"' in part:
                    next_url = part[part.find("<") + 1 : part.find(">")]
                    break

            url = next_url

    except Exception as e:
        logging.error(e)
        if not suppress_errors:
            raise e

    return quarantined_objects


def filter_and_print_steps_by_quarantined(
    ctx: BuildkiteContext, all_steps, skip_quarantined_steps, mute_quarantined_steps
):
    if (skip_quarantined_steps or mute_quarantined_steps) and not ctx.config.no_skip:
        filtered_steps, skipped_steps, muted_steps = filter_steps_by_quarantined(
            ctx, all_steps, skip_quarantined_steps, mute_quarantined_steps
        )
        if skipped_steps:
            for step in skipped_steps:
                logging.info(f"Skipped step: {step.get('label') or 'unnamed'}")
        if muted_steps:
            for step in muted_steps:
                logging.info(f"Muted step: {step.get('label') or 'unnamed'}")

        return filtered_steps
    return all_steps


def filter_steps_by_quarantined(
    ctx: BuildkiteContext, steps, skip_quarantined_steps, mute_quarantined_steps
):
    if (not skip_quarantined_steps and not mute_quarantined_steps) or ctx.config.no_skip:
        return steps, [], []

    filtered_steps = []
    skipped_steps = []
    muted_steps = []

    for step in steps:
        # Handle both individual steps and step groups
        if "group" in step:
            # For step groups, check if any of the steps in the group are quarantined
            group_steps = step["steps"]
            filtered_group_steps = []
            for group_step in group_steps:
                label = group_step.get("label") or ""
                if label in skip_quarantined_steps:
                    skipped_steps.append(group_step)
                elif label in mute_quarantined_steps:
                    group_step["soft_fail"] = True
                    muted_steps.append(group_step)
                    filtered_group_steps.append(group_step)
                else:
                    filtered_group_steps.append(group_step)

            if filtered_group_steps:
                step["steps"] = filtered_group_steps
                filtered_steps.append(step)
        else:
            # For individual steps, check if the step key is in quarantined list
            label = step.get("label") or ""
            if label in skip_quarantined_steps:
                skipped_steps.append(step)
            elif label in mute_quarantined_steps:
                step["soft_fail"] = True
                muted_steps.append(step)
                filtered_steps.append(step)
            else:
                filtered_steps.append(step)

    return filtered_steps, skipped_steps, muted_steps
