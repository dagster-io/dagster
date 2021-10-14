from dagster import op, Any, In, Nothing, OpDefinition, Out
import logging


def operator_to_op(airflow_op, capture_logs=False, return_output=False) -> OpDefinition:
    @op(ins={"start_after": In(Nothing)}, out=Out(Any) if return_output else Out(Nothing))
    def converted_op(context):
        airflow_op._log = context.log
        if capture_logs:
            root_logger = logging.getLogger()
            root_logger.addHandler(context.log._dagster_handler)
            print("y" * 10)
            print(root_logger.handlers)
        output = airflow_op.execute({})
        if capture_logs:
            root_logger.removeHandler(context.log._dagster_handler)
        if return_output:
            return output

    return converted_op
