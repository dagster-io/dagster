import dagster as dg


@dg.asset(code_version="v4")
def versioned_number():
    value = 20
    return dg.Output(value, data_version=dg.DataVersion(str(value)))


@dg.asset(code_version="v1")
def multiplied_number(versioned_number):
    return versioned_number * 2
