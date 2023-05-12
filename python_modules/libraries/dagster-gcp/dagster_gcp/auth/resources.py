import base64
import json
from typing import List, Optional

import dagster._check as check
import google.auth
from dagster import ConfigurableResource
from google.oauth2 import service_account
from pydantic import Field, root_validator


class GoogleAuthResource(ConfigurableResource):
    service_account_file: Optional[str] = Field(default=None, description="")
    service_account_info: Optional[str] = Field(default=None, description="")
    scopes: Optional[List[str]] = Field(default=None, description="")
    quota_project_id: Optional[str] = Field(default=None, description="")

    @root_validator
    def validate_authentication_method(cls, values):
        auths_set = 0
        auths_set += 1 if values.get("service_account_file") is not None else 0
        auths_set += 1 if values.get("service_account_info") is not None else 0

        check.invariant(
            auths_set <= 1,
            (
                "Incorrect config: Cannot provide both service_account_file and"
                " service_account_info authentication to GoogleAuthResource."
            ),
        )

        return values

    def get_credentials(self):
        if self.service_account_file is not None:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file
            )
            if self.scopes is not None:
                credentials = credentials.with_scopes(self.scopes)

            return credentials

        if self.service_account_info is not None:
            decoded_service_account_info = json.loads(base64.b64decode(self.service_account_info))
            credentials = service_account.Credentials.from_service_account_info(
                decoded_service_account_info
            )

            if self.scopes is not None:
                credentials = credentials.with_scopes(self.scopes)

            return credentials

        credentials, _ = google.auth.default(
            scopes=self.scopes, quota_project_id=self.quota_project_id
        )

        return credentials
