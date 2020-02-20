# This should be an enum once we make our own buildkite AMI with py3
class SupportedPython(object):
    V3_8 = "3.8.1"
    V3_7 = "3.7.6"
    V3_6 = "3.6.10"
    V3_5 = "3.5.8"
    V2_7 = "2.7.17"


# See: https://github.com/dagster-io/dagster/issues/1960
SupportedPythons = [
    SupportedPython.V3_7,
    SupportedPython.V3_6,
    SupportedPython.V3_5,
    SupportedPython.V2_7,
]

# See: https://github.com/dagster-io/dagster/issues/1960
SupportedPython3s = [SupportedPython.V3_7, SupportedPython.V3_6, SupportedPython.V3_5]

SupportPython3sEx35 = [SupportedPython.V3_7, SupportedPython.V3_6]
