import base64
import io
import json
import os
import subprocess
import sys
import tempfile
import traceback
from typing import Any, Dict

import boto3
from dagster_pipes import PipesMappingParamsLoader, PipesS3MessageWriter, open_dagster_pipes


class LambdaFunctions:
    @staticmethod
    def trunc_logs(event, context):
        sys.stdout.write("O" * 1024 * 3)
        sys.stderr.write("E" * 1024 * 3)

    @staticmethod
    def small_logs(event, context):
        print("S" * event["size"])  # noqa: T201

    @staticmethod
    def pipes_basic(event, _lambda_context):
        with open_dagster_pipes(params_loader=PipesMappingParamsLoader(event)) as dagster_context:
            dagster_context.report_asset_materialization(metadata={"meta": "data"})

    @staticmethod
    def pipes_messy_logs(event, _lambda_context):
        with open_dagster_pipes(params_loader=PipesMappingParamsLoader(event)) as dagster_context:
            # without buffering this would get lost
            dagster_context.report_asset_materialization(metadata={"meta": "data"})
            sys.stderr.write("E" * 1024 * 4)

    @staticmethod
    def pipes_s3_messages(event, _lambda_context):
        s3_client = boto3.client(
            "s3",
            region_name="us-east-1",
            endpoint_url="http://localhost:5193",
        )
        with open_dagster_pipes(
            params_loader=PipesMappingParamsLoader(event),
            message_writer=PipesS3MessageWriter(
                client=s3_client,
                interval=0.001,
            ),
        ) as dagster_context:
            dagster_context.report_asset_materialization(metadata={"meta": "data"})

    @staticmethod
    def error(event, _lambda_context):
        raise Exception("boom")


class FakeLambdaContext:
    pass


LOG_TAIL_LIMIT = 4096


class FakeLambdaClient:
    def invoke(self, **kwargs):
        # emulate lambda constraints with a subprocess invocation
        # * json serialized "Payload" result
        # * 4k log output as base64 "LogResult"

        with tempfile.TemporaryDirectory() as tempdir:
            in_path = os.path.join(tempdir, "in.json")
            out_path = os.path.join(tempdir, "out.json")
            log_path = os.path.join(tempdir, "logs")

            with open(in_path, "w") as f:
                f.write(kwargs["Payload"])

            with open(log_path, "w") as log_file:
                result = subprocess.run(
                    [
                        sys.executable,
                        os.path.join(os.path.dirname(__file__), "fake_lambda.py"),
                        kwargs["FunctionName"],
                        in_path,
                        out_path,
                    ],
                    check=False,
                    env={},  # env vars part of lambda fn definition, can't vary at runtime
                    stdout=log_file,
                    stderr=log_file,
                )

            response: dict[str, Any] = {}

            if result.returncode == 42:
                response["FunctionError"] = "Unhandled"

            elif result.returncode != 0:
                with open(log_path) as f:
                    print(f.read())  # noqa: T201
                result.check_returncode()

            with open(out_path, "rb") as f:
                payload = io.BytesIO(f.read())

            response["Payload"] = payload

            if kwargs.get("LogType") == "Tail":
                logs_len = os.path.getsize(log_path)
                with open(log_path, "rb") as log_file:
                    if logs_len > LOG_TAIL_LIMIT:
                        log_file.seek(-LOG_TAIL_LIMIT, os.SEEK_END)

                    outro = log_file.read()

                log_result = base64.encodebytes(outro)

                response["LogResult"] = log_result

        return response


if __name__ == "__main__":
    assert len(sys.argv) == 4, "python fake_lambda.py <fn_name> <in_path> <out_path>"
    _, fn_name, in_path, out_path = sys.argv

    event = json.load(open(in_path))
    fn = getattr(LambdaFunctions, fn_name)

    val = None
    return_code = 0
    try:
        val = fn(event, FakeLambdaContext())
    except Exception as e:
        tb = traceback.TracebackException.from_exception(e)
        val = {
            "errorMessage": str(tb),
            "errorType": tb.exc_type.__name__,
            "stackTrace": tb.stack.format(),
            "requestId": "fake-request-id",
        }
        return_code = 42

    with open(out_path, "w") as f:
        json.dump(val, f)

    sys.exit(return_code)
