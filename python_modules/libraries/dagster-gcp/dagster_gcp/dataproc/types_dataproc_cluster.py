"""NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT

@generated

Produced via:
parse_dataproc_configs.py \

"""


from dagster import Enum, EnumValue

Component = Enum(
    name="Component",
    enum_values=[
        EnumValue("COMPONENT_UNSPECIFIED", description="""Unspecified component."""),
        EnumValue("ANACONDA", description="""The Anaconda python distribution."""),
        EnumValue(
            "HIVE_WEBHCAT",
            description="""The Hive Web HCatalog (the REST service for
        accessing HCatalog).""",
        ),
        EnumValue("JUPYTER", description="""The Jupyter Notebook."""),
        EnumValue("ZEPPELIN", description="""The Zeppelin notebook."""),
    ],
)
