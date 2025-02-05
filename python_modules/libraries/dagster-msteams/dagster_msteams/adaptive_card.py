from typing import Any


class AdaptiveCard:
    """Class to contruct a MS Teams adaptive card for posting Dagster messages."""

    def __init__(self, adaptive_card_version: str = "1.5"):
        """Constructs an adaptive card with the given version.

        Args:
            adaptive_card_version (str): The version of the adaptive card to use. Defaults to "1.5".
        """
        self._body = []
        self._adaptive_card_version = adaptive_card_version

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
                        "version": self._adaptive_card_version,
                        "body": self._body,
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

    def add_attachment(self, text_message: str) -> None:
        """Appends a text message to the adaptive card."""
        self._body.append(self._build_text_block(text_message))
