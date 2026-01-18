from typing import Any

import dagster as dg
import torch
from sklearn.model_selection import train_test_split
from torchvision import datasets, transforms

from project_ml.defs.constants import DATA_DIR, MNIST_MEAN, MNIST_STD, RANDOM_SEED, VALIDATION_SPLIT


# start_raw_data_loading
@dg.asset(
    description="Download and load raw MNIST dataset",
    group_name="data_processing",
)
def raw_mnist_data(context) -> dict[str, Any]:
    """Download the raw MNIST dataset."""
    transform = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize((MNIST_MEAN,), (MNIST_STD,)),  # MNIST mean and std
        ]
    )

    # Download training data
    train_dataset = datasets.MNIST(
        root=str(DATA_DIR), train=True, download=True, transform=transform
    )

    # Download test data
    test_dataset = datasets.MNIST(
        root=str(DATA_DIR), train=False, download=True, transform=transform
    )

    # Convert to tensors
    train_data = torch.stack([train_dataset[i][0] for i in range(len(train_dataset))])
    train_labels = torch.tensor([train_dataset[i][1] for i in range(len(train_dataset))])

    test_data = torch.stack([test_dataset[i][0] for i in range(len(test_dataset))])
    test_labels = torch.tensor([test_dataset[i][1] for i in range(len(test_dataset))])

    context.log.info(f"Loaded {len(train_data)} training samples and {len(test_data)} test samples")

    return {
        "train_data": train_data,
        "train_labels": train_labels,
        "test_data": test_data,
        "test_labels": test_labels,
    }


# end_raw_data_loading


# start_data_preprocessing
@dg.asset(
    description="Preprocess MNIST images for training",
    group_name="data_processing",
)
def processed_mnist_data(context, raw_mnist_data: dict[str, Any]) -> dict[str, torch.Tensor]:
    """Process MNIST data and create train/validation split."""
    train_data = raw_mnist_data["train_data"]
    train_labels = raw_mnist_data["train_labels"]
    test_data = raw_mnist_data["test_data"]
    test_labels = raw_mnist_data["test_labels"]

    # Create validation split from training data
    train_data, val_data, train_labels, val_labels = train_test_split(
        train_data,
        train_labels,
        test_size=VALIDATION_SPLIT,
        random_state=RANDOM_SEED,
        stratify=train_labels,
    )

    # Convert back to tensors
    train_data = torch.tensor(train_data)
    val_data = torch.tensor(val_data)
    train_labels = torch.tensor(train_labels)
    val_labels = torch.tensor(val_labels)

    context.add_output_metadata(
        {
            "train_samples": len(train_data),
            "val_samples": len(val_data),
            "test_samples": len(test_data),
            "image_shape": str(train_data.shape[1:]),
            "num_classes": len(torch.unique(train_labels)),
        }
    )

    context.log.info(
        f"Processed data - Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}"
    )

    return {
        "train_data": train_data,
        "val_data": val_data,
        "train_labels": train_labels,
        "val_labels": val_labels,
        "test_data": test_data,
        "test_labels": test_labels,
    }


# end_data_preprocessing
