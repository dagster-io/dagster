import uuid
from functools import cached_property

from dagster_sigma import SigmaBaseUrl, SigmaOrganization
from dagster_sigma.components.sigma_organization_component import (
    SigmaOrganizationComponent,
)
from dagster_sigma.translator import SigmaDataset, SigmaOrganizationData, SigmaWorkbook


class MockSigmaOrganization(SigmaOrganization):
    async def build_organization_data(
        self,
        sigma_filter=None,
        fetch_column_data: bool = True,
        fetch_lineage_data: bool = True,
    ) -> SigmaOrganizationData:
        """Returns mock Sigma organization data."""
        # Create mock workbook
        workbook = SigmaWorkbook(
            properties={
                "workbookId": str(uuid.uuid4()),
                "name": "Sample Workbook",
                "url": f"{self.base_url}/workbook/sample",
                "path": "My Documents",
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z",
            },
            datasets_by_inode={},
            tables_by_inode={},
        )

        # Create mock dataset
        dataset = SigmaDataset(
            properties={
                "datasetId": str(uuid.uuid4()),
                "name": "Orders Dataset",
                "url": f"{self.base_url}/dataset/orders",
                "description": "Sample orders dataset",
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z",
            }
        )

        return SigmaOrganizationData(
            workbooks=[workbook],
            datasets=[dataset],
        )


class MockSigmaComponent(SigmaOrganizationComponent):
    @cached_property
    def organization_resource(self) -> MockSigmaOrganization:
        return MockSigmaOrganization(**self.organization.model_dump())


def test_mock_sigma_organization() -> None:
    """Test that the mock Sigma organization returns the expected data."""
    import asyncio

    organization = MockSigmaOrganization(
        base_url=SigmaBaseUrl.AWS_US.value,
        client_id="test_client_id",
        client_secret="test_client_secret",
    )

    organization_data = asyncio.run(organization.build_organization_data())

    # Verify we have the expected content
    assert len(organization_data.workbooks) == 1
    assert len(organization_data.datasets) == 1

    # Verify specific content
    assert organization_data.workbooks[0].properties["name"] == "Sample Workbook"
    assert organization_data.datasets[0].properties["name"] == "Orders Dataset"
