from typing import Any, Optional

from dagster_msteams.utils import Link


class AdaptiveCard:
    """Class to contruct a MS Teams adaptive card for posting Dagster messages."""

    def __init__(self, message: str, link: Optional[Link] = None):
        if link:
            message += f" [{link.text}]({link.url})"

        self.payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": {
                        "type": "AdaptiveCard",
                        "version": "1.0",
                        "body": [self._build_text_block(message)],
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
