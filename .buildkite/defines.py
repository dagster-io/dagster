# This should be an enum once we make our own buildkite AMI with py3
class SupportedPython:
    V3_8 = "3.8.1"
    V3_7 = "3.7.6"
    V3_6 = "3.6.10"
    V3_5 = "3.5.8"
    V2_7 = "2.7.17"


SupportedPythons = [
    SupportedPython.V2_7,
    SupportedPython.V3_5,
    SupportedPython.V3_6,
    SupportedPython.V3_7,
    SupportedPython.V3_8,
]

# See: https://github.com/dagster-io/dagster/issues/1960
SupportedPythonsNo38 = [
    SupportedPython.V2_7,
    SupportedPython.V3_5,
    SupportedPython.V3_6,
    SupportedPython.V3_7,
]


# See: https://github.com/dagster-io/dagster/issues/1960
SupportedPython3sNo38 = [SupportedPython.V3_7, SupportedPython.V3_6, SupportedPython.V3_5]

SupportedPython3s = [
    SupportedPython.V3_5,
    SupportedPython.V3_6,
    SupportedPython.V3_7,
    SupportedPython.V3_8,
]


TOX_MAP = {
    SupportedPython.V3_8: "py38",
    SupportedPython.V3_7: "py37",
    SupportedPython.V3_6: "py36",
    SupportedPython.V3_5: "py35",
    SupportedPython.V2_7: "py27",
}
