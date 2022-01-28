from bollinger.jobs.bollinger_sda import bollinger_sda


def test_bollinger_sda():
    bollinger_sda.execute_in_process()
