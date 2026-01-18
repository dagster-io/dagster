from collections.abc import Mapping


class Card:
    """Class to contruct a MS Teams Hero card for posting dagster messages."""

    def __init__(self):
        self.payload = {"type": "message", "attachments": []}

    @property
    def type(self):
        return self.payload["type"]

    @property
    def attachments(self):
        return self.payload["attachments"]

    def _create_attachment(self, text_message: str) -> Mapping:
        content = {
            "title": "Dagster Pipeline Alert",
            "text": text_message,
        }
        content_type = "application/vnd.microsoft.card.hero"
        return {"contentType": content_type, "content": content}

    def add_attachment(self, text_message: str):
        hero_card_attachment = self._create_attachment(text_message)
        self.payload["attachments"].append(hero_card_attachment)
