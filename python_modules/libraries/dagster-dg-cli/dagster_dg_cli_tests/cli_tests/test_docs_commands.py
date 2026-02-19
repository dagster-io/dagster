import json

from dagster_test.dg_utils.utils import ProxyRunner, assert_runner_result


def test_utils_integrations_json():
    with ProxyRunner.test() as runner:
        result = runner.invoke("utils", "integrations", "--json")
        assert_runner_result(result)
        output_json = json.loads(result.stdout)
        assert isinstance(output_json, list)
        assert isinstance(output_json[0], dict)
