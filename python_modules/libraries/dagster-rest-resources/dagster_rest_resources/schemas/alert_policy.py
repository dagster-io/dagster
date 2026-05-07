from typing import Any

from dagster_rest_resources.schemas.util import DgApiList


class DgApiAlertPolicyDocument(DgApiList[dict[str, Any]]):
    pass


class DgApiAlertPolicySyncResult(DgApiList[str]):
    pass
