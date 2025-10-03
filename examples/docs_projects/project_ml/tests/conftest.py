import pytest
import torch
from dagster import build_asset_context


@pytest.fixture
def mock_context():
    """Create a proper Dagster context for testing."""
    return build_asset_context()


@pytest.fixture
def mock_mnist_data():
    """Create mock MNIST data for testing."""
    return {
        "train_data": torch.randn(1000, 1, 28, 28),
        "train_labels": torch.randint(0, 10, (1000,)),
        "test_data": torch.randn(200, 1, 28, 28),
        "test_labels": torch.randint(0, 10, (200,)),
    }
