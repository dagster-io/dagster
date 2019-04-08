from dagster import check, lambda_solid, OutputDefinition


def define_stub_solid(name, value):
    check.str_param(name, 'name')

    @lambda_solid(name=name, output=OutputDefinition())
    def _stub():
        return value

    return _stub
