from dagster_blueprints.op_job_blueprint import OpJobBlueprint, OpModel


def test_op_job_blueprint():
    messages = []

    class MyOpModel(OpModel):
        message: str

        def compute_fn(self, context) -> None:
            messages.append(self.message)

    op_job_blueprint = OpJobBlueprint(
        name="my_job",
        ops={
            "op1": MyOpModel(message="hello1"),
            "op2": MyOpModel(message="hello2", deps=["op1"]),
        },
    )

    blueprint_defs = op_job_blueprint.build_defs()
    defs = blueprint_defs.to_definitions()
    my_job = defs.get_job_def("my_job")
    my_job.execute_in_process()
