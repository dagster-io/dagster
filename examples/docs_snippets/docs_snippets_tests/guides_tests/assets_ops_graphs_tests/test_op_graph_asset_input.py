from dagster import InputContext, IOManager, OutputContext
from docs_snippets.guides.dagster.assets_ops_graphs.op_graph_asset_input import (
    send_emails_job,
)


def test_send_emails_job():
    class EmailsIOManager(IOManager):
        def load_input(self, context: InputContext):
            ...

        def handle_output(self, context: OutputContext, obj):
            ...

    send_emails_job.graph.execute_in_process(
        resources={"io_manager": EmailsIOManager()}
    )
