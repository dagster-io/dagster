import time

import boto3
import botocore.exceptions

from dagster import check


class ECSClient:
    """
    This class governs everything you need to generate, run, and track a specific task on ECS

    Args:
        region_name (Optional[str]):  which AWS region you're running on
        key_id (Optional[str]): the AWS access key ID to use
        access_key (Optional[str]): the AWS access key going with that key_id
        launch_type (Optional[str]): whether to use EC2 or FARGATE for the task
        grab_logs (Optional[bool]):  whether to pull down ECS logs
        starter_client (boto3.client): starter ecs client, used for mocking
        starter_log_client (boto3.client): starter log client, used for mocking


    TODO: find ECS specific logs, if they exist -- right now logs are stdout and stderr
    """

    def __init__(
        self,
        region_name="us-east-2",
        key_id="",
        access_key="",
        launch_type="FARGATE",
        starter_client=None,
        starter_log_client=None,
        grab_logs=True,
    ):
        self.key_id = check.str_param(key_id, "key_id")
        self.region_name = check.str_param(region_name, "region_name")
        self.access_key = check.str_param(access_key, "access_key")
        self.launch_type = check.str_param(launch_type, "launch_type")
        self.account_id = "123412341234"
        self.grab_logs = check.bool_param(grab_logs, "grab_logs")
        self.task_definition_arn = None
        self.tasks = []
        self.tasks_done = []
        self.offset = -1
        self.container_name = None
        self.ecs_logs = dict()
        self.logs_messages = dict()
        self.warnings = []
        self.cluster = None
        if starter_client is None:
            self.ecs_client = self.make_client("ecs")
            self.account_id = boto3.client("sts").get_caller_identity().get("Account")
        else:
            self.ecs_client = starter_client
        if starter_log_client is None:
            self.log_client = self.make_client("logs")
        else:
            self.log_client = starter_log_client
        self.set_cluster()

    def make_client(self, client_type, **kwargs):
        """
        constructs an ECS client object with the given params

        Args:
            client_type (str): which ECS client you're trying to produce
            **kwargs: any add'l keyword params
        Returns:
            client: the constructed client object
        """
        if self.key_id != "":
            clients = boto3.client(
                client_type,
                aws_access_key_id=self.key_id,
                aws_secret_access_key=self.access_key,
                region_name=self.region_name,
                **kwargs
            )
        else:
            clients = boto3.client(client_type, region_name=self.region_name, **kwargs)

        return clients

    def set_cluster(self):
        """
        sets the task's compute cluster to be the first available/default compute cluster.
        """
        self.cluster = self.ecs_client.list_clusters()["clusterArns"][0]

    def set_and_register_task(
        self,
        command,
        entrypoint,
        family="echostart",
        containername="basictest",
        imagename="httpd:2.4",
        memory="512",
        cpu="256",
    ):
        """
        Generates a task corresponding to a given docker image, command, and entry point
        while setting instance attrs accordingly (logging and task attrs).
        Args:
            command (List[str]): Command to run on container
            entrypoint (List[str]): Entrypoint for container
            family (Optional[str]): what task family you want this task revising
            containername (Optional[str]):  what you want the container the task is on to be called
            imagename (Optional[str]): the URI for the docker image
            memory (Optional[str]): how much memory (in MB) the task needs
            cpu (Optional[str]): how much CPU (in vCPU) the task needs
        """
        fmtstr = family + str(self.offset + 1)
        try:
            self.log_client.create_log_group(logGroupName="/ecs/{}".format(fmtstr))
        except botocore.exceptions.ClientError as e:
            self.warnings.append(str(e))
        basedict = {
            "executionRoleArn": "arn:aws:iam::{}:role/ecsTaskExecutionRole".format(self.account_id),
            "containerDefinitions": [
                {
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/{}".format(fmtstr),
                            "awslogs-region": "us-east-2",
                            "awslogs-stream-prefix": "ecs",
                        },
                    },
                    "entryPoint": entrypoint,
                    "portMappings": [{"hostPort": 8080, "protocol": "tcp", "containerPort": 8080}],
                    "command": command,
                    "cpu": 0,
                    "environment": [{"name": "TEST", "value": "end"}],
                    "image": imagename,
                    "name": containername,
                }
            ],
            "placementConstraints": [],
            "memory": memory,
            "family": family,
            "requiresCompatibilities": ["FARGATE"],
            "networkMode": "awsvpc",
            "cpu": cpu,
        }
        response = self.ecs_client.register_task_definition(**basedict)
        arn = response["taskDefinition"]["taskDefinitionArn"]
        self.task_definition_arn = arn
        self.container_name = containername

    def run_task(self, **kwargs):
        """
        sets this client's task running.

        TODO: explicitly add overrides as params here for cpu, command, and environment vars

        Args:
            **kwargs: Any add'l params you want the task to have
        """
        taskdict = self.ecs_client.run_task(
            taskDefinition=self.task_definition_arn,
            launchType=self.launch_type,
            cluster=self.cluster,
            **kwargs
        )
        task = taskdict["tasks"][0]
        container = task["containers"][0]
        running_task_arn = container["taskArn"]
        self.tasks.append(running_task_arn)
        self.tasks_done.append(False)
        self.offset += 1

    def check_if_done(self, offset=0):
        """
        polls ECS to see if the task is complete, pulling down logs if so

        TODO:  handle pagination for 100+ tasks
        Args:
             offset (int): which task to check for

        Returns:
             boolean corresponding to completion
        """
        if self.tasks_done[offset]:
            return True
        response = self.ecs_client.describe_tasks(tasks=self.tasks, cluster=self.cluster)
        resp = response["tasks"][offset]
        if resp["lastStatus"] == "STOPPED":
            if self.grab_logs:
                check_arn = resp["taskDefinitionArn"]
                taskDefinition = self.ecs_client.describe_task_definition(taskDefinition=check_arn)[
                    "taskDefinition"
                ]
                logconfig = taskDefinition["containerDefinitions"][0]["logConfiguration"]["options"]
                streamobj = self.log_client.describe_log_streams(
                    logGroupName=logconfig["awslogs-group"],
                    logStreamNamePrefix=logconfig["awslogs-stream-prefix"],
                )
                logs = self.log_client.get_log_events(
                    logGroupName=logconfig["awslogs-group"],
                    logStreamName=streamobj["logStreams"][-1]["logStreamName"],
                )
                self.ecs_logs[offset] = logs["events"]
                self.logs_messages[offset] = [log["message"] for log in logs["events"]]
            self.tasks_done[offset] = True
            return True
        return False

    def spin_til_done(self, offset=0, time_delay=5):
        """
        spinpolls the ECS servers to test if the task is done

        Args:
            offset (int): the offset of the task within the task array
            time_delay (int): how long to wait between polls, seconds
        """
        while not self.check_if_done(offset=offset):
            time.sleep(time_delay)

    def spin_all(self, time_delay=5):
        """
        spinpolls all generated tasks
        Args:
            time_delay (int): how long to wait between polls, seconds
        """
        for i in range(self.offset + 1):
            self.spin_til_done(offset=i, time_delay=time_delay)


if __name__ == "__main__":
    import yaml

    with open("config.yaml") as f:
        data = yaml.load(f, Loader=yaml.SafeLoader)

    testclient = ECSClient()
    testclient.set_and_register_task(
        ["echo start"], ["/bin/bash", "-c"], family="multimessage",
    )
    networkConfiguration = {
        "awsvpcConfiguration": {
            "subnets": ["subnet-0f3b1467",],
            "securityGroups": ["sg-08627da7435350fa6",],
            "assignPublicIp": "ENABLED",
        }
    }
    testclient.run_task(networkConfiguration=networkConfiguration)

    testclient.set_and_register_task(
        ["echo middle"], ["/bin/bash", "-c"], family="multimessage",
    )
    testclient.run_task(networkConfiguration=networkConfiguration)
    testclient.set_and_register_task(
        ["echo $TEST"], ["/bin/bash", "-c"], family="multimessage",
    )
    testclient.run_task(networkConfiguration=networkConfiguration)
    testclient.spin_til_done(offset=2)
    testclient.spin_til_done(offset=1)
    testclient.spin_til_done()
    print(testclient.logs_messages)  # pylint: disable=print-call
