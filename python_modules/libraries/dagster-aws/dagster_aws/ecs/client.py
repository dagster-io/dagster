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
        starter_client (boto3.client): starter ecs client, used for mocking
        starter_log_client (boto3.client): starter log client, used for mocking
    """

    def __init__(
        self,
        region_name='us-east-2',
        key_id='',
        access_key='',
        launch_type='FARGATE',
        starter_client=None,
        starter_log_client=None,
    ):
        self.key_id = check.str_param(key_id, 'key_id')
        self.region_name = check.str_param(region_name, 'key_id')
        self.access_key = check.str_param(access_key, 'key_id')
        self.launch_type = check.str_param(launch_type, 'key_id')
        self.task_definition_arn = None
        self.tasks = None
        self.container_name = None
        self.log_group_name = None
        self.ecs_logs = None
        self.logs_messages = None
        self.warnings = []
        self.log_stream_name = None
        self.cluster = None
        if starter_client is None:
            self.ecs_client = self.make_client('ecs')
        else:
            self.ecs_client = starter_client
        if starter_log_client is None:
            self.log_client = self.make_client('logs')
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
        if self.key_id != '':
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
        self.cluster = self.ecs_client.list_clusters()['clusterArns'][0]

    def set_and_register_task(
        self,
        command,
        entrypoint,
        family='echostart',
        containername='basictest',
        imagename="httpd:2.4",
        memory='512',
        cpu='256',
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
        try:
            self.log_client.create_log_group(logGroupName="/ecs/{}".format(family))
        except botocore.exceptions.ClientError as e:
            self.warnings.append(str(e))
        basedict = {
            "executionRoleArn": "arn:aws:iam::968703565975:role/ecsTaskExecutionRole",
            "containerDefinitions": [
                {
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/{}".format(family),
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
        task = taskdict['tasks'][0]
        container = task['containers'][0]
        running_task_arn = container["taskArn"]
        self.tasks = [running_task_arn]
        taskDefinition = self.ecs_client.describe_task_definition(
            taskDefinition=self.task_definition_arn
        )['taskDefinition']
        logconfig = taskDefinition['containerDefinitions'][0]['logConfiguration']['options']
        streamobj = self.log_client.describe_log_streams(
            logGroupName=logconfig['awslogs-group'],
            logStreamNamePrefix=logconfig['awslogs-stream-prefix'],
        )
        self.log_group_name = logconfig['awslogs-group']
        self.log_stream_name = streamobj['logStreams'][-1]['logStreamName']

    def check_if_done(self):
        """
        polls ECS to see if the task is complete, pulling down logs if so

        TODO:  handle pagination for 100+ tasks
        Returns:
             boolean corresponding to completion
        """
        response = self.ecs_client.describe_tasks(tasks=self.tasks, cluster=self.cluster)
        if response['tasks'][0]['lastStatus'] == 'STOPPED':
            logs = self.log_client.get_log_events(
                logGroupName=self.log_group_name, logStreamName=self.log_stream_name
            )
            self.ecs_logs = logs['events']
            self.logs_messages = [log['message'] for log in self.ecs_logs]
            return True
        return False

    def spin_til_done(self, time_delay=5):
        """
        spinpolls the ECS servers to test if the task is done

        Args:
            time_delay (int): how long to wait between polls, seconds
        """
        while not self.check_if_done():
            time.sleep(time_delay)


if __name__ == "__main__":
    import yaml

    with open('config.yaml') as f:
        data = yaml.load(f, Loader=yaml.SafeLoader)

    testclient = ECSClient()
    testclient.set_and_register_task(
        ["echo $TEST; echo start; echo middle"], ["/bin/bash", "-c"], family='multimessage',
    )
    networkConfiguration = {
        'awsvpcConfiguration': {
            'subnets': ['subnet-0f3b1467',],
            'securityGroups': ['sg-08627da7435350fa6',],
            'assignPublicIp': 'ENABLED',
        }
    }
    testclient.run_task(networkConfiguration=networkConfiguration)
    testclient.spin_til_done()
    assert " ".join(testclient.logs_messages) == '\"end\" start middle'
