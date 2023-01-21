"""NOTE: THIS FILE IS AUTO-GENERATED. DO NOT EDIT.

@generated

Produced via:
parse_dataproc_configs.py \

"""


from dagster import Enum, EnumValue

Substate = Enum(
    name="Substate",
    enum_values=[
        EnumValue("UNSPECIFIED", description="""The job substate is unknown."""),
        EnumValue(
            "SUBMITTED",
            description="""The Job is submitted to the agent.Applies to RUNNING
        state.""",
        ),
        EnumValue(
            "QUEUED",
            description="""The Job has been received and is awaiting execution (it
        may be waiting for a condition to be met). See the "details" field for the reason for the
        delay.Applies to RUNNING state.""",
        ),
        EnumValue(
            "STALE_STATUS",
            description="""The agent-reported status is out of date, which may
        be caused by a loss of communication between the agent and Cloud Dataproc. If the agent does
        not send a timely update, the job will fail.Applies to RUNNING state.""",
        ),
    ],
)

State = Enum(
    name="State",
    enum_values=[
        EnumValue("STATE_UNSPECIFIED", description="""Status is unspecified."""),
        EnumValue("NEW", description="""Status is NEW."""),
        EnumValue("NEW_SAVING", description="""Status is NEW_SAVING."""),
        EnumValue("SUBMITTED", description="""Status is SUBMITTED."""),
        EnumValue("ACCEPTED", description="""Status is ACCEPTED."""),
        EnumValue("RUNNING", description="""Status is RUNNING."""),
        EnumValue("FINISHED", description="""Status is FINISHED."""),
        EnumValue("FAILED", description="""Status is FAILED."""),
        EnumValue("KILLED", description="""Status is KILLED."""),
    ],
)
