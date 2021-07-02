from dagster_msteams.card import Card


def test_add_attachment_to_card():
    card = Card()
    card.add_attachment("Pipeline failure !!!")
    card.add_attachment("Pipeline success !!!")
    assert len(card.attachments) == 2
    assert card.attachments[0]["contentType"] == "application/vnd.microsoft.card.hero"
    assert card.attachments[0]["content"]["subtitle"] == "Pipeline failure !!!"
    assert card.type == "message"
