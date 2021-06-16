from collections import defaultdict

from botocore.stub import Stubber


def stubbed(function):
    """
    A decorator that activates/deactivates the Stubber and makes sure all
    expected calls are made.

    The general pattern for stubbing a new method is:

    @stubbed
    def method(self, **kwargs):
        self.stubber.add_response(
            method="method", # Name of the method being stubbed
            service_response={}, # Stubber validates the resposne shape
            expected_params(**kwargs), # Stubber validates the params
        )
        self.client.method(**kwargs) # "super" (except we're not actually
                                     # subclassing anything)
    """

    def wrapper(*args, **kwargs):
        self = args[0]

        # If we're the first stub, activate:
        if not self.stub_count:
            self.stubber.activate()

        self.stub_count += 1
        try:
            response = function(*args, **kwargs)
            # If we're the outermost stub, clean up
            self.stub_count -= 1
            if not self.stub_count:
                self.stubber.deactivate()
                self.stubber.assert_no_pending_responses()
            return response
        except Exception as ex:
            # Exceptions should reset the stubber
            self.stub_count = 0
            self.stubber.deactivate()
            self.stubber = Stubber(self.client)
            raise ex

    return wrapper


class StubbedEcs:
    """
    A class that stubs ECS responses using botocore's Stubber:
    https://botocore.amazonaws.com/v1/documentation/api/latest/reference/stubber.html

    Stubs are minimally sufficient for testing existing Dagster ECS behavior;
    consequently, not all endpoints are stubbed and not all stubbed endpoints
    are stubbed exhaustively.

    Stubber validates that we aren't passing invalid parameters or returning
    an invalid response shape. Additionally, some resources (tasks, tags,
    task_definitions) are stored in the instance which allows methods to have
    some minimal interaction - for example, you can't run a task if you haven't
    first created a task definition.

    We can't extend botocore.client.ECS directly. Eventually, we might want to
    register these methods as events instead of maintaing our own StubbedEcs
    class:
    https://boto3.amazonaws.com/v1/documentation/api/latest/guide/events.html
    """

    def __init__(self, boto3_client):
        self.client = boto3_client
        self.stubber = Stubber(self.client)

        self.task_definitions = defaultdict(list)
        self.stub_count = 0

    @stubbed
    def register_task_definition(self, **kwargs):
        family = kwargs.get("family")
        # Revisions are 1 indexed
        revision = len(self.task_definitions[family]) + 1
        arn = self._task_definition_arn(family, revision)

        task_definition = {
            "family": family,
            "revision": revision,
            "taskDefinitionArn": arn,
            **kwargs,
        }

        self.task_definitions[family].append(task_definition)

        self.stubber.add_response(
            method="register_task_definition",
            service_response={"taskDefinition": task_definition},
            expected_params={**kwargs},
        )
        return self.client.register_task_definition(**kwargs)

    def _arn(self, resource_type, resource_id):
        return f"arn:aws:ecs:us-east-1:1234567890:{resource_type}/{resource_id}"

    def _task_definition_arn(self, family, revision):
        return self._arn("task-definition", f"{family}:{revision}")
