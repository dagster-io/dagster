# This should be an enum once we make our own buildkite AMI with py3
class SupportedPython:
    V3_8 = "3.8.3"
    V3_7 = "3.7.8"
    V3_6 = "3.6.11"
    V2_7 = "2.7.18"


SupportedPythons = [
    SupportedPython.V2_7,
    SupportedPython.V3_6,
    SupportedPython.V3_7,
    SupportedPython.V3_8,
]


SupportedPython3s = [
    SupportedPython.V3_6,
    SupportedPython.V3_7,
    SupportedPython.V3_8,
]


TOX_MAP = {
    SupportedPython.V3_8: "py38",
    SupportedPython.V3_7: "py37",
    SupportedPython.V3_6: "py36",
    SupportedPython.V2_7: "py27",
}

####################################################################################################
# Dagster images
#
# These timestamps are generated with:
# datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%S")
####################################################################################################

# Update this when releasing a new version of our integration image
# Per README.md, run the integration build image pipeline
# and then find the tag of the created images. A string
# like the following will be in that tag.
INTEGRATION_IMAGE_VERSION = "2020-09-01T134240"

# Keep this fixed. Do not update when updating snapshots Only update when updating the base
# integration image which should be less frequent
INTEGRATION_BASE_VERSION = "2020-07-03T094007"

# Update this when releasing a new version of our unit image
# Per README.md, run the unit build image pipeline
# and then find the tag of the created images. A string
# like the following will be in that tag.
UNIT_IMAGE_VERSION = "2020-09-25T230550"
