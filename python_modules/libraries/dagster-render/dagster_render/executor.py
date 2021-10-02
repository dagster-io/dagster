from dagster import Executor

class RenderExecutor(Executor):
    def execute(self, pipeline_context, execution_plan):
        ...

    def retries(self):
        ...
