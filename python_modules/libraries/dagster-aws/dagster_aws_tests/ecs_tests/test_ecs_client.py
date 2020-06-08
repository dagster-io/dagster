import os

import pytest
from dagster_aws.ecs import client


@pytest.mark.skipif(
    'AWS_ECS_TEST_DO_IT_LIVE' not in os.environ,
    reason='This test is slow and requires a live ECS cluster; run only upon explicit request',
)
def test_success():
    testclient = client.ECSClient()
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
    assert len(testclient.logs_messages) == 3
    assert testclient.logs_messages[2] == 'middle'


if __name__ == '__main__':
    test_success()
