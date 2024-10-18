import requests


class DbtCloudInstance:
    def __init__(
        self, account_prefix: str, region: str, account_id: str, personal_token: str, name: str
    ):
        self.account_prefix = account_prefix
        self.account_id = account_id
        self.personal_token = personal_token
        self.name = name
        self.region = region

    def get_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "Accept": "application/json",
                "Authorization": f"Token {self.personal_token}",
            }
        )
        return session

    def get_account_url(self) -> str:
        return (
            f"https://{self.account_prefix}.{self.region}.dbt.com/api/v3/accounts/{self.account_id}"
        )

    def test_connection(self) -> None:
        session = self.get_session()
        response = session.get(
            f"{self.get_account_url()}/projects/?limit=10&offset=5",
        )
        if response.status_code != 200:
            raise Exception(f"Failed to connect to dbt cloud: {response.text}")
