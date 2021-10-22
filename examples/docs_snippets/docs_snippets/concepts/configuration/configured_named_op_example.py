from dagster import Field, In, Int, List, configured, job, op


# start_configured_named
@op(
    config_schema={
        "is_sample": Field(bool, is_required=False, default_value=False),
    },
    ins={"xs": In(List[Int])},
)
def get_dataset(context, xs):
    if context.op_config["is_sample"]:
        return xs[:5]
    else:
        return xs


# If we want to use the same op configured in multiple ways in the same job,
# we have to specify unique names when configuring them:
sample_dataset = configured(get_dataset, name="sample_dataset")({"is_sample": True})
full_dataset = configured(get_dataset, name="full_dataset")({"is_sample": False})


@job
def datasets():
    sample_dataset()
    full_dataset()


# end_configured_named
