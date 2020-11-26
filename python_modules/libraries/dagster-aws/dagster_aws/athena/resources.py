import uuid

from botocore.stub import Stubber


class AthenaError(Exception):
    pass


class AthenaTimeout(AthenaError):
    pass


class AthenaResource:
    def __init__(self, client, workgroup_name="primary", retry_interval=5, max_retries=120):
        self.client = client
        self.workgroup_name = workgroup_name
        self.max_retries = max_retries
        self.retry_interval = retry_interval

    def execute_query(self, query_string):
        execution_id = self.client.start_query_execution(
            QueryString=query_string, WorkGroup=self.workgroup_name
        )["QueryExecutionId"]
        self._poll(execution_id)

        return True

    def _poll(self, execution_id):
        retries = self.max_retries
        state = "QUEUED"

        while retries >= 0 and state in ["QUEUED", "RUNNING"]:
            execution = self.client.get_query_execution(QueryExecutionId=execution_id)[
                "QueryExecution"
            ]
            state = execution["Status"]["State"]
            if self.max_retries > 0:
                retries -= 1

        if retries < 0:
            raise AthenaTimeout()

        if state != "SUCCEEDED":
            raise AthenaError(execution["Status"]["StateChangeReason"])


class FakeAthenaResource(AthenaResource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.retry_interval = 0
        self.stubber = Stubber(self.client)

    def execute_query(self, query_string, expected_states=None):  # pylint: disable=arguments-differ
        if not expected_states:
            expected_states = ["QUEUED", "RUNNING", "SUCCEEDED"]

        self.stubber.activate()

        execution_id = str(uuid.uuid4())
        self._stub_start_query_execution(execution_id, query_string)
        self._stub_get_query_execution(execution_id, expected_states)

        result = super().execute_query(query_string)

        self.stubber.deactivate()
        self.stubber.assert_no_pending_responses()

        return result

    def _stub_start_query_execution(self, execution_id, query_string):
        self.stubber.add_response(
            method="start_query_execution",
            service_response={"QueryExecutionId": execution_id},
            expected_params={"QueryString": query_string, "WorkGroup": self.workgroup_name},
        )

    def _stub_get_query_execution(self, execution_id, states):
        for state in states:
            self.stubber.add_response(
                method="get_query_execution",
                service_response={
                    "QueryExecution": {
                        "Status": {"State": state, "StateChangeReason": "state change reason"}
                    }
                },
                expected_params={"QueryExecutionId": execution_id},
            )
