# This should be an enum once we make our own buildkite AMI with py3
class SupportedPython:
    V3_7 = "3.7"
    V3_6 = "3.6"
    V3_5 = "3.5"
    V2_7 = "2.7"


SupportedPythons = [
    SupportedPython.V3_7,
    SupportedPython.V3_6,
    SupportedPython.V3_5,
    SupportedPython.V2_7,
]

SupportedPython3s = [SupportedPython.V3_7, SupportedPython.V3_6, SupportedPython.V3_5]

IMAGE_VERSION_MAP = {
    SupportedPython.V3_7: "3.7.3",
    SupportedPython.V3_6: "3.6.8",
    SupportedPython.V3_5: "3.5.7",
    SupportedPython.V2_7: "2.7.16",
}
