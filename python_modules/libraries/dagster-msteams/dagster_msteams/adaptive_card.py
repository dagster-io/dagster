from typing import Any, Optional

from dagster_msteams.utils import Link


class AdaptiveCard:
    """Class to contruct a MS Teams adaptive card for posting Dagster messages."""

    def __init__(self):
        self._text_blocks = []

    @property
    def payload(self) -> dict[str, Any]:
        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": {
                        "type": "AdaptiveCard",
                        "version": "1.0",
                        "body": self._text_blocks,
                    },
                }
            ],
        }

    def _build_text_block(self, text: str) -> dict[str, Any]:
        return {
            "type": "TextBlock",
            "text": text,
            "wrap": True,
        }

    def add_attachment(self, text_message: str, link: Optional[Link] = None) -> None:
        if link:
            text_message += f" [{link.text}]({link.url})"

        self._text_blocks.append(self._build_text_block(text_message))
