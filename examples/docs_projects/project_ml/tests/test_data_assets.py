import torch
from project_ml.defs.assets.data_assets import raw_mnist_data


def test_raw_mnist_data_basic(mock_context):
    """Basic test that raw MNIST data loads without errors."""
    data = raw_mnist_data(mock_context)

    # Just check that we get some data back
    assert "train_data" in data
    assert "test_data" in data
    assert isinstance(data["train_data"], torch.Tensor)
