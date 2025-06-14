import dagster as dg


@dg.asset(code_version="v5")
def versioned_number():
    value = 10 + 10
    return dg.Output(value, data_version=dg.DataVersion(str(value)))


@dg.asset(code_version="v1")
def multiplied_number(versioned_number):
    return versioned_number * 2
