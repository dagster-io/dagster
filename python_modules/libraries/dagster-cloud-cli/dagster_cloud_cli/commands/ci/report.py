from . import state

STATUS_IMAGES = {
    state.LocationStatus.success: (
        "https://raw.githubusercontent.com/dagster-io/dagster-cloud-action/main/assets/success.png"
    ),
    state.LocationStatus.pending: (
        "https://raw.githubusercontent.com/dagster-io/dagster-cloud-action/main/assets/pending.png"
    ),
    state.LocationStatus.failed: (
        "https://raw.githubusercontent.com/dagster-io/dagster-cloud-action/main/assets/failed.png"
    ),
}

STATUS_MESSAGES = {
    state.LocationStatus.success: "View in Cloud",
    state.LocationStatus.pending: "Building...",
    state.LocationStatus.failed: "Deploy failed",
}


def markdown_report(location_states: list[state.LocationState]):
    markdown = []
    markdown.append(
        """
| Location          | Status          | Link    | Updated         |
| ----------------- | --------------- | ------- | --------------- | 
"""
    )
    for location_state in location_states:
        if not location_state.selected or not location_state.history:
            continue
        last_status = location_state.history[-1]
        image_url = STATUS_IMAGES[last_status.status]
        message = STATUS_MESSAGES[last_status.status]
        if last_status.status == state.LocationStatus.success or not location_state.status_url:
            link_url = f"{location_state.url}/{location_state.deployment_name}/locations"
        else:
            link_url = location_state.status_url
        status_image = f'[<img src="{image_url}" width=25 height=25/>]({link_url})'
        status_message = f"[{message}]({link_url})"

        time_str = last_status.timestamp.strftime("%b %d, %Y at %I:%M %p (%Z)")
        markdown.append(
            f"| {location_state.location_name} | {status_image}  | {status_message}  |"
            f" {time_str} |\n"
        )

    return "".join(markdown)
