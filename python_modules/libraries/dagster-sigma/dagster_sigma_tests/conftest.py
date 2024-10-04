import uuid
from typing import Any, Dict, List

import pytest
import responses
from dagster_sigma import SigmaBaseUrl


@pytest.fixture(name="sigma_auth_token")
def sigma_auth_fixture() -> str:
    fake_access_token: str = uuid.uuid4().hex

    responses.add(
        method=responses.POST,
        url=f"{SigmaBaseUrl.AWS_US.value}/v2/auth/token",
        json={"access_token": fake_access_token},
        status=200,
    )

    return fake_access_token


def _build_paginated_response(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "entries": items,
        "hasMore": False,
        "total": len(items),
        "nextPage": None,
    }


SAMPLE_WORKBOOK_DATA = {
    "workbookId": "4ea60fe9-f487-43b0-aa7a-3ef43ca3a90e",
    "workbookUrlId": "2opi6VLEne4BaPyj00US50",
    "createdBy": "8TUQL5YbOwebkUGS0SAdqxlU5R0gD",
    "updatedBy": "8TUQL5YbOwebkUGS0SAdqxlU5R0gD",
    "createdAt": "2024-09-12T21:22:49.072Z",
    "updatedAt": "2024-09-12T22:20:39.848Z",
    "name": "Sample Workbook",
    "url": "https://app.sigmacomputing.com/dagster-labs/workbook/2opi6VLEne4BaPyj00US50",
    "path": "My Documents",
    "latestVersion": 5,
    "ownerId": "8TUQL5YbOwebkUGS0SAdqxlU5R0gD",
}

SAMPLE_DATASET_INODE = "inode-Iq557kfHN8KRu76HdGSWi"
SAMPLE_DATASET_DATA = {
    "datasetId": "178a6bb5-c0e7-4bef-a739-f12710492f16",
    "createdBy": "8TUQL5YbOwebkUGS0SAdqxlU5R0gD",
    "updatedBy": "8TUQL5YbOwebkUGS0SAdqxlU5R0gD",
    "createdAt": "2024-09-12T21:16:17.830Z",
    "updatedAt": "2024-09-12T21:19:31.000Z",
    "name": "Orders Dataset",
    "description": "Wow, cool orders dataset",
    "url": "https://app.sigmacomputing.com/dagster-labs/b/Iq557kfHN8KRu76HdGSWi",
}


@pytest.fixture(name="sigma_sample_data")
def sigma_sample_data_fixture() -> None:
    # Single workbook, dataset
    responses.add(
        method=responses.GET,
        url="https://aws-api.sigmacomputing.com/v2/workbooks",
        json=_build_paginated_response([SAMPLE_WORKBOOK_DATA]),
        status=200,
    )
    responses.add(
        method=responses.GET,
        url="https://aws-api.sigmacomputing.com/v2/datasets",
        json=_build_paginated_response([SAMPLE_DATASET_DATA]),
        status=200,
    )

    responses.add(
        method=responses.GET,
        url="https://aws-api.sigmacomputing.com/v2/workbooks/4ea60fe9-f487-43b0-aa7a-3ef43ca3a90e/pages",
        json=_build_paginated_response([{"pageId": "qwMyyHBCuC", "name": "Page 1"}]),
        status=200,
    )
    responses.add(
        method=responses.GET,
        url="https://aws-api.sigmacomputing.com/v2/workbooks/4ea60fe9-f487-43b0-aa7a-3ef43ca3a90e/pages/qwMyyHBCuC/elements",
        json=_build_paginated_response(
            [
                {
                    "elementId": "_MuHPbskp0",
                    "type": "table",
                    "name": "sample elementl",
                    "columns": [
                        "Order Id",
                        "Customer Id",
                        "workbook renamed date",
                        "Modified Date",
                    ],
                    "vizualizationType": "levelTable",
                },
                {
                    "elementId": "V29pknzHb6",
                    "type": "visualization",
                    "name": "Count of Order Date by Status",
                    "columns": [
                        "Order Id",
                        "Customer Id",
                        "Order Date",
                        "Status",
                        "Modified Date",
                        "Count of Order Date",
                    ],
                    "vizualizationType": "bar",
                },
            ]
        ),
        status=200,
    )
    responses.add(
        method=responses.GET,
        url="https://aws-api.sigmacomputing.com/v2/workbooks/4ea60fe9-f487-43b0-aa7a-3ef43ca3a90e/lineage/elements/_MuHPbskp0",
        json={
            "dependencies": {
                "qy_ARjTKcT": {
                    "nodeId": "qy_ARjTKcT",
                    "type": "sheet",
                    "name": "sample elementl",
                    "elementId": "_MuHPbskp0",
                },
                "inode-Iq557kfHN8KRu76HdGSWi": {
                    "nodeId": "inode-Iq557kfHN8KRu76HdGSWi",
                    "type": "dataset",
                    "name": "Orders Dataset",
                },
            },
            "edges": [
                {"source": "inode-Iq557kfHN8KRu76HdGSWi", "target": "qy_ARjTKcT", "type": "source"}
            ],
        },
        status=200,
    )
    responses.add(
        method=responses.GET,
        url="https://aws-api.sigmacomputing.com/v2/workbooks/4ea60fe9-f487-43b0-aa7a-3ef43ca3a90e/elements/_MuHPbskp0/columns",
        json=_build_paginated_response(
            [
                {"columnId": "inode-Iq557kfHN8KRu76HdGSWi/Order Id", "label": "Order Id"},
                {"columnId": "inode-Iq557kfHN8KRu76HdGSWi/Customer Id", "label": "Customer Id"},
                {
                    "columnId": "inode-Iq557kfHN8KRu76HdGSWi/Order Date",
                    "label": "workbook renamed date",
                },
                {"columnId": "inode-Iq557kfHN8KRu76HdGSWi/Modified Date", "label": "Modified Date"},
            ]
        ),
        status=200,
    )
    responses.add(
        method=responses.GET,
        url="https://aws-api.sigmacomputing.com/v2/workbooks/4ea60fe9-f487-43b0-aa7a-3ef43ca3a90e/lineage/elements/V29pknzHb6",
        json={
            "dependencies": {
                "SBvQYKT6ui": {
                    "nodeId": "SBvQYKT6ui",
                    "type": "sheet",
                    "name": "Count of Order Date by Status",
                    "elementId": "V29pknzHb6",
                },
                "inode-Iq557kfHN8KRu76HdGSWi": {
                    "nodeId": "inode-Iq557kfHN8KRu76HdGSWi",
                    "type": "dataset",
                    "name": "Orders Dataset",
                },
            },
            "edges": [
                {"source": "inode-Iq557kfHN8KRu76HdGSWi", "target": "SBvQYKT6ui", "type": "source"}
            ],
        },
        status=200,
    )
    responses.add(
        method=responses.GET,
        url="https://aws-api.sigmacomputing.com/v2/workbooks/4ea60fe9-f487-43b0-aa7a-3ef43ca3a90e/elements/V29pknzHb6/columns",
        json=_build_paginated_response(
            [
                {"columnId": "inode-Iq557kfHN8KRu76HdGSWi/Order Id", "label": "Order Id"},
                {"columnId": "inode-Iq557kfHN8KRu76HdGSWi/Customer Id", "label": "Customer Id"},
                {"columnId": "inode-Iq557kfHN8KRu76HdGSWi/Order Date", "label": "Order Date"},
                {"columnId": "inode-Iq557kfHN8KRu76HdGSWi/Status", "label": "Status"},
                {"columnId": "inode-Iq557kfHN8KRu76HdGSWi/Modified Date", "label": "Modified Date"},
                {"columnId": "VBKAHQgx58", "label": "Count of Order Date"},
            ]
        ),
        status=200,
    )
    responses.add(
        method=responses.GET,
        url="https://aws-api.sigmacomputing.com/v2/workbooks/4ea60fe9-f487-43b0-aa7a-3ef43ca3a90e/queries",
        json=_build_paginated_response(
            [
                {
                    "elementId": "_MuHPbskp0",
                    "name": "sample elementl",
                    "sql": 'select ORDER_ID_7 "Order Id", CUSTOMER_ID_8 "Customer Id", CAST_DATE_TO_DATETIME_9 "workbook renamed date", CAST_DATE_TO_DATETIME_11 "Modified Date" from (select ORDER_ID ORDER_ID_7, CUSTOMER_ID CUSTOMER_ID_8, ORDER_DATE::timestamp_ltz CAST_DATE_TO_DATETIME_9, ORDER_DATE::timestamp_ltz CAST_DATE_TO_DATETIME_11 from (select * from TESTDB.JAFFLE_SHOP.STG_ORDERS STG_ORDERS limit 1000) Q1) Q2 limit 1000\n\n-- Sigma \u03a3 {"request-id":"69ac9a35-64b3-4840-a53d-3aed43a575ec","email":"ben@dagsterlabs.com"}',
                },
                {
                    "elementId": "V29pknzHb6",
                    "name": "Count of Order Date by Status",
                    "sql": 'with Q1 as (select ORDER_ID, CUSTOMER_ID, STATUS, ORDER_DATE::timestamp_ltz CAST_DATE_TO_DATETIME_5, ORDER_DATE::timestamp_ltz CAST_DATE_TO_DATETIME_6 from TESTDB.JAFFLE_SHOP.STG_ORDERS STG_ORDERS) select STATUS_10 "Status", COUNT_22 "Count of Order Date", ORDER_ID_7 "Order Id", CUSTOMER_ID_8 "Customer Id", CAST_DATE_TO_DATETIME_7 "Order Date", CAST_DATE_TO_DATETIME_8 "Modified Date" from (select Q3.ORDER_ID_7 ORDER_ID_7, Q3.CUSTOMER_ID_8 CUSTOMER_ID_8, Q3.CAST_DATE_TO_DATETIME_7 CAST_DATE_TO_DATETIME_7, Q3.STATUS_10 STATUS_10, Q3.CAST_DATE_TO_DATETIME_8 CAST_DATE_TO_DATETIME_8, Q6.COUNT_22 COUNT_22, Q6.STATUS_11 STATUS_11 from (select ORDER_ID ORDER_ID_7, CUSTOMER_ID CUSTOMER_ID_8, CAST_DATE_TO_DATETIME_6 CAST_DATE_TO_DATETIME_7, STATUS STATUS_10, CAST_DATE_TO_DATETIME_5 CAST_DATE_TO_DATETIME_8 from Q1 Q2 order by STATUS_10 asc limit 1000) Q3 left join (select count(CAST_DATE_TO_DATETIME_7) COUNT_22, STATUS_10 STATUS_11 from (select CAST_DATE_TO_DATETIME_6 CAST_DATE_TO_DATETIME_7, STATUS STATUS_10 from Q1 Q4) Q5 group by STATUS_10) Q6 on equal_null(Q3.STATUS_10, Q6.STATUS_11)) Q8 order by STATUS_10 asc limit 1000\n\n-- Sigma \u03a3 {"request-id":"69ac9a35-64b3-4840-a53d-3aed43a575ec","email":"ben@dagsterlabs.com"}',
                },
            ]
        ),
        status=200,
    )

    responses.add(
        method=responses.GET,
        url="https://aws-api.sigmacomputing.com/v2/members",
        json=_build_paginated_response(
            [
                {
                    "organizationId": "4d55c33f-dbb8-4426-9d70-97742e01f002",
                    "memberId": "8TUQL5YbOwebkUGS0SAdqxlU5R0gD",
                    "memberType": "admin",
                    "firstName": "Ben",
                    "lastName": "Pankow",
                    "email": "ben@dagsterlabs.com",
                    "profileImgUrl": None,
                    "createdBy": "8TUQL5YbOwebkUGS0SAdqxlU5R0gD",
                    "updatedBy": "8TUQL5YbOwebkUGS0SAdqxlU5R0gD",
                    "createdAt": "2024-09-12T20:44:19.736Z",
                    "updatedAt": "2024-09-12T20:44:19.736Z",
                    "homeFolderId": "bd7e1b16-dad3-45d4-91e7-5687be2819cc",
                    "userKind": "internal",
                },
                {
                    "organizationId": "4d55c33f-dbb8-4426-9d70-97742e01f002",
                    "memberId": "SigmaSchedulerRobot",
                    "memberType": "admin",
                    "firstName": "Scheduler",
                    "lastName": "User",
                    "email": "scheduler-robot@sigmacomputing.com",
                    "profileImgUrl": None,
                    "createdBy": "SigmaSchedulerRobot",
                    "updatedBy": "SigmaSchedulerRobot",
                    "createdAt": "2024-09-12T20:44:20.182Z",
                    "updatedAt": "2024-09-12T20:44:20.182Z",
                    "homeFolderId": "4537ec2e-ced7-4aa6-b511-ed0437e0165f",
                    "userKind": "internal",
                },
            ]
        ),
        status=200,
    )
