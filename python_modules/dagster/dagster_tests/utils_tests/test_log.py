import logging

from dagster.utils.log import quieten


def test_quieten(caplog):
    logging.log(msg="Now you see me!", level=logging.WARNING)
    with quieten():
        logging.log(msg="Now you don't!", level=logging.WARNING)
    logging.log(msg="Now you see me again!", level=logging.WARNING)

    assert "Now you see me!" in caplog.text
    assert "Now you don't!" not in caplog.text
    assert "Now you see me again!" in caplog.text


def test_quieten_quiet(caplog):
    logging.log(msg="Now you see me!", level=logging.WARNING)
    with quieten(quiet=False):
        logging.log(msg="Now you see me too!", level=logging.WARNING)
    logging.log(msg="Now you see me again!", level=logging.WARNING)

    assert "Now you see me!" in caplog.text
    assert "Now you see me too!" in caplog.text
    assert "Now you see me again!" in caplog.text
