from typing import NamedTuple, Optional


class MSTeamsHyperlink(NamedTuple):
    text: str
    url: str


def build_message_with_link(
    is_legacy_webhook: bool, text: str, link: Optional[MSTeamsHyperlink]
) -> str:
    if link:
        if is_legacy_webhook:
            return f"{text} <a href='{link.url}'>{link.text}</a>"
        else:
            return f"{text} [{link.text}]({link.url})"

    return text
