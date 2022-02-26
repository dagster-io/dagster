from dagster import resource
import subprocess
import os
import sys

from cdktf import App, TerraformStack

from .imports.aws.s3 import S3Bucket
from .imports.aws import AwsProvider


class Stack(TerraformStack):
    def __init__(self, app: App, stack_name: str):
        super().__init__(app, stack_name)
        AwsProvider(self, "Aws", region="us-west-2")
        self.app = app
        self.stack_name = stack_name

    def synth(self):
        self.app.synth()

    def deploy(self):
        os.chdir(f"{sys.path[0]}/stacks/{self.stack_name}/")
        subprocess.call(["terraform", "init"])
        subprocess.call(["terraform", "apply", "-auto-approve"])

    def destroy(self):
        os.chdir(f"{sys.path[0]}/stacks/{self.stack_name}/")
        subprocess.call(["terraform", "destroy", "-auto-approve"])


@resource(
    config_schema={
        "name": str,
    }
)
def terraform_stack(init_context):
    app = App(outdir="./")
    return Stack(app, init_context.resource_config["name"])


class Resource:
    def __init__(self, definition, **kwargs):
        self.definition = definition(**kwargs)
        self.config = kwargs


@resource(
    required_resource_keys={"terraform_stack"},
    config_schema={
        "id": str,
        "bucket": str,
    },
)
def s3_bucket(init_context):
    init_context.log.warn(init_context.resource_config)
    bucket = Resource(
        S3Bucket,
        scope=init_context.resources.terraform_stack,
        id=init_context.resource_config["id"],
        bucket=init_context.resource_config["bucket"],
    )
    init_context.log.info("synthesizing terraform json...")
    init_context.resources.terraform_stack.synth()
    init_context.log.info("deploying terraform stack...")
    init_context.resources.terraform_stack.deploy()
    yield bucket
    init_context.log.info("destroying terraform stack...")
    init_context.resources.terraform_stack.destroy()
