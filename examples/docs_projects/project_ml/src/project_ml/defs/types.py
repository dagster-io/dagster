from typing import Any, TypedDict

import torch


class ModelData(TypedDict):
    model: torch.nn.Module
    config: dict
    accuracy: float
    timestamp: str
    model_architecture: str


class DataBatch(TypedDict):
    train_data: torch.Tensor
    train_labels: torch.Tensor
    val_data: torch.Tensor
    val_labels: torch.Tensor
    test_data: torch.Tensor
    test_labels: torch.Tensor


class EvaluationResult(TypedDict):
    test_accuracy: float
    predictions: list[int]
    labels: list[int]
    classification_report: dict[str, Any]
    model_info: dict[str, str]
