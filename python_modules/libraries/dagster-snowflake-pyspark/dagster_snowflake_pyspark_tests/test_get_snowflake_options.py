import base64

import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from dagster._check import CheckError
from dagster._core.storage.db_io_manager import TableSlice
from dagster_snowflake_pyspark.constants import SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER_PYSPARK
from dagster_snowflake_pyspark.snowflake_pyspark_type_handler import _get_snowflake_options

TEST_PRIVATE_KEY = (
    "-----BEGIN PRIVATE KEY-----\n"
    "MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQCcfVZZrx48J56a\n"
    "CWFo4uTt7pwBRMuTv+U416Z4HG/d73vqxHfAKx2+lKs9tLTTjIkl62rCxZ3rx6TU\n"
    "b0NnQs+4S+DB/qPtGEVOzIeEDvllIWAgluE3TMtUyLEwiYgpTreZ4RxPilyZGSHX\n"
    "fvPdqEIfLFcW8Knnv5Skr512NuIJRiGBqUewO6h/sK8Qc2iqpWyaC1K0cLHPNn5g\n"
    "gLRSprHvs9id1gtQ5BzfNKyUWrxDuf58K7cXijFs0091bGYbO7KyNr2w0YohvNC0\n"
    "sFAu0eqCfl3TamkX0FFAY51Wr1d7q3rncrzZ3HWyIPx8JDlnousqSxrJa37tiiOR\n"
    "9O8cpr5PAgMBAAECggEAA2nSd9tTgAFnOrnop4aHcs8pFPgArsTZRZ+ikG0iXYdr\n"
    "PwgxCn6GRBFvGMX3ycN/fFXBuuTfmHR+2mlg4YA6Eq2JBgI9Zh8I5/qbHBzNgNC1\n"
    "DZDs8a1ZpAxKnSHq1+fRJmicGvoMIgTD0bUBsbyJUK/BaI0wT49EuUDhYOI6lPQr\n"
    "Z9ySE97+6sFYCxRCdcIMkSocOrqmcWEpe1RKFTsHNBgiCZd8hq1kz5b12FkI+/Db\n"
    "aGXt91XErSepyCEOlB7Y2rVWyd4g5cqK/nW821a0Wz1CJDiblEml7TmWlW68utdH\n"
    "9J5xNzlsdgjVx/0fiLvND5s2CJzgzX3wWpgoFk6aFQKBgQDVpyASoZ4hA9ACbtw+\n"
    "hOAoZTqXmATuMD/3qUCtZBwT3h6oAYU90Z5YZBOT9fPGAk1WEiLL1gPGD3t86Sj7\n"
    "4Ns3kAecDD76vFp++luDy+CAFPcyJJhMcvgotYUa2l8dZLViMPxq2VzNREUE9BNw\n"
    "eZr0nBESIaKjN1trw3B4xRKejQKBgQC7gbb5V9ju8wLTaqWp1LvOa6w3g2pj5TwJ\n"
    "FxnO9vBCWyA5hki5DWPEIDIe68mqxrDqc0lp0hfVTmsV1LtGM1D+qRbGz3pWGomq\n"
    "pHEJcLizahrYrmr+2GE1XqIDgvi3KmPSWc4C6B5K9Hohd/cVEORzqXz8a3MAtza2\n"
    "/rBlESo3SwKBgQC1ZrzYlNiJ9465Qh9GBdO8+JYS+EPXaKgnQ1Fi5sjgJYup4gCb\n"
    "SEtFiVMGIaHk0TeQiL16jC+QDr0uhVkC4xu9xVBwsgUXJq0/epoRAR2QIjzwGhol\n"
    "bsg86EInVpnDfypyQF1Q61TcA8cGOaX3rYhff9MOrfhE1E+O49Wu9MSmUQKBgQCo\n"
    "gZn92oSJuLoBZQYb6aIdj4XlHaSuwYOCZ9A5vpGMEHiVOaiBJRdTWduxDhTd9FFp\n"
    "YNHI15WzjBWQOO1T2SogsbRWVn6Kgq7VO5KZ+UMDeYdG0vg0riAt5i2TGlCJyv6K\n"
    "O0p4MkGG+s4G5diWhefISbiY37cqHXx+V8QOD67woQKBgQDHc9kw4gS5/5oJTfzL\n"
    "X7j1rjh+YbUqS3Y5OLD6brqta0tNxmuW8zAZ9cNHKq1IHOfeXEhiid5U34sG9RnL\n"
    "IZytfLjyVlAgI/YkQrXdaAVJxNI+UG3NYfxuwrFdq5+6sAayVFGwamybhMoTyzo8\n"
    "nUYa4x8V3H7W/cVTZI7HzhQKOQ==\n"
    "-----END PRIVATE KEY-----\n"
)


@pytest.fixture
def snowflake_config() -> dict[str, str]:
    return {
        "account": "account",
        "user": "user",
        "password": "password",
        "database": "database",
        "warehouse": "warehouse",
    }


@pytest.fixture
def table_slice() -> TableSlice:
    return TableSlice("table_name", "schema_name", "database_name")


def test_get_snowflake_options(snowflake_config, table_slice):
    options = _get_snowflake_options(snowflake_config, table_slice)
    assert options == {
        "sfURL": "account.snowflakecomputing.com",
        "sfUser": "user",
        "sfPassword": "password",
        "sfDatabase": "database",
        "sfWarehouse": "warehouse",
        "sfSchema": "schema_name",
        "APPLICATION": SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER_PYSPARK,
    }


def test_get_snowflake_options_with_private_key(snowflake_config, table_slice):
    del snowflake_config["password"]
    snowflake_config["private_key"] = TEST_PRIVATE_KEY

    options = _get_snowflake_options(snowflake_config, table_slice)
    assert "sfPassword" not in options
    assert options["pem_private_key"] != TEST_PRIVATE_KEY
    loaded_key = serialization.load_der_private_key(
        base64.b64decode(options["pem_private_key"]),
        password=None,
        backend=default_backend(),
    )
    assert loaded_key is not None

    assert options["sfURL"] == "account.snowflakecomputing.com"
    assert options["sfUser"] == "user"
    assert options["sfDatabase"] == "database"
    assert options["sfWarehouse"] == "warehouse"
    assert options["sfSchema"] == "schema_name"
    assert options["APPLICATION"] == SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER_PYSPARK


def test_missing_warehouse(snowflake_config, table_slice):
    del snowflake_config["warehouse"]

    with pytest.raises(CheckError):
        _get_snowflake_options(snowflake_config, table_slice)
