from dagster import Int, logger


def test_dagster_type_logger_decorator_config():
    @logger(Int)
    def dagster_type_logger_config(_):
        raise Exception('not called')

    assert dagster_type_logger_config.config_field.config_type.given_name == 'Int'

    @logger(int)
    def python_type_logger_config(_):
        raise Exception('not called')

    assert python_type_logger_config.config_field.config_type.given_name == 'Int'
