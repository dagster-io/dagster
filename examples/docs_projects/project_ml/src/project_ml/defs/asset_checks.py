from collections.abc import Iterable
from typing import Any

import dagster as dg
import torch


# Data Quality Checks
@dg.asset_check(asset="raw_mnist_data")
def check_mnist_data_completeness(context, raw_mnist_data: dict[str, Any]) -> dg.AssetCheckResult:
    """Check that MNIST dataset has expected number of samples."""
    train_samples = len(raw_mnist_data.get("train_data", []))
    test_samples = len(raw_mnist_data.get("test_data", []))
    total_samples = train_samples + test_samples

    passed = total_samples == 70000  # MNIST total
    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "train_samples": train_samples,
            "test_samples": test_samples,
            "total_samples": total_samples,
            "expected_total": 70000,
        },
    )


@dg.asset_check(asset="raw_mnist_data")
def check_mnist_data_labels(context, raw_mnist_data: dict[str, Any]) -> dg.AssetCheckResult:
    """Check that labels are in valid range [0,9] for digit classification."""
    train_labels = raw_mnist_data.get("train_labels", [])
    test_labels = raw_mnist_data.get("test_labels", [])

    all_labels = torch.cat([train_labels, test_labels])
    min_label = int(all_labels.min())
    max_label = int(all_labels.max())

    passed = min_label >= 0 and max_label <= 9
    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "min_label": min_label,
            "max_label": max_label,
            "label_range_valid": passed,
        },
    )


@dg.asset_check(asset="processed_mnist_data")
def check_data_split_proportions(
    context, processed_mnist_data: dict[str, torch.Tensor]
) -> dg.AssetCheckResult:
    """Check that train/validation split proportions are correct."""
    train_samples = len(processed_mnist_data.get("train_data", []))
    val_samples = len(processed_mnist_data.get("val_data", []))
    test_samples = len(processed_mnist_data.get("test_data", []))

    # MNIST has 60k training, 10k test, so validation should be ~12k (20% of 60k)
    expected_val = 12000
    val_tolerance = 1000  # Allow some flexibility

    passed = abs(val_samples - expected_val) <= val_tolerance
    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "train_samples": train_samples,
            "val_samples": val_samples,
            "test_samples": test_samples,
            "expected_val": expected_val,
            "tolerance": val_tolerance,
        },
    )


# Model Quality Checks
@dg.asset_check(asset="digit_classifier")
def check_model_weights_finite(context, digit_classifier) -> dg.AssetCheckResult:
    """Check that model weights are finite (no NaN or Inf values)."""
    nan_count = 0
    inf_count = 0

    for name, param in digit_classifier.named_parameters():
        if param.requires_grad:
            if torch.isnan(param).any():
                nan_count += 1
            if torch.isinf(param).any():
                inf_count += 1

    passed = nan_count == 0 and inf_count == 0
    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "parameters_with_nan": nan_count,
            "parameters_with_inf": inf_count,
            "total_parameters": sum(p.numel() for p in digit_classifier.parameters()),
        },
    )


@dg.asset_check(asset="digit_classifier")
def check_model_prediction_shape(context, digit_classifier) -> dg.AssetCheckResult:
    """Check that model can make predictions with correct output shape."""
    try:
        test_input = torch.randn(1, 1, 28, 28)
        with torch.no_grad():
            output = digit_classifier(test_input)
            expected_shape = (1, 10)  # batch_size=1, num_classes=10
            passed = output.shape == expected_shape

            return dg.AssetCheckResult(
                passed=passed,
                metadata={
                    "actual_shape": str(output.shape),
                    "expected_shape": str(expected_shape),
                    "output_dtype": str(output.dtype),
                },
            )
    except Exception as e:
        return dg.AssetCheckResult(passed=False, metadata={"error": str(e)})


# Evaluation Quality Checks
@dg.asset_check(asset="model_evaluation")
def check_accuracy_reasonable(context, model_evaluation: dict[str, Any]) -> dg.AssetCheckResult:
    """Check that model accuracy is within reasonable bounds."""
    test_accuracy = model_evaluation.get("test_accuracy", 0.0)

    # Accuracy should be between 0 and 1, and above a reasonable threshold
    passed = 0 <= test_accuracy <= 1 and test_accuracy > 0.5

    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "test_accuracy": test_accuracy,
            "min_threshold": 0.5,
            "accuracy_in_bounds": 0 <= test_accuracy <= 1,
        },
    )


@dg.asset_check(asset="model_evaluation")
def check_evaluation_completeness(context, model_evaluation: dict[str, Any]) -> dg.AssetCheckResult:
    """Check that all expected evaluation metrics are present."""
    required_keys = ["test_accuracy", "predictions", "labels", "classification_report"]
    missing_keys = [key for key in required_keys if key not in model_evaluation]

    passed = len(missing_keys) == 0
    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "required_keys": required_keys,
            "missing_keys": missing_keys,
            "present_keys": list(model_evaluation.keys()),
        },
    )


# Production Deployment Checks
@dg.asset_check(asset="production_digit_classifier", blocking=True)
def check_production_model_quality(context, production_digit_classifier) -> dg.AssetCheckResult:
    """Check that production model meets deployment criteria (blocking check)."""
    if production_digit_classifier is None:
        return dg.AssetCheckResult(passed=False, metadata={"error": "Production model is None"})

    # Verify model can make predictions
    try:
        test_input = torch.randn(1, 1, 28, 28)
        with torch.no_grad():
            output = production_digit_classifier(test_input)
            passed = output.shape == (1, 10)

            return dg.AssetCheckResult(
                passed=passed,
                metadata={
                    "model_type": str(type(production_digit_classifier)),
                    "prediction_shape": str(output.shape),
                    "deployment_ready": passed,
                },
            )
    except Exception as e:
        return dg.AssetCheckResult(passed=False, metadata={"error": str(e)})


# Multi-asset check for prediction quality
@dg.multi_asset_check(
    specs=[
        dg.AssetCheckSpec(name="check_prediction_format", asset="batch_digit_predictions"),
        dg.AssetCheckSpec(name="check_confidence_scores", asset="batch_digit_predictions"),
    ]
)
def check_prediction_quality(
    context, batch_digit_predictions: dict[str, list]
) -> Iterable[dg.AssetCheckResult]:
    """Check multiple aspects of prediction quality."""
    predictions = batch_digit_predictions.get("predictions", [])
    confidences = batch_digit_predictions.get("confidences", [])

    # Check prediction format
    valid_predictions = all(0 <= pred <= 9 for pred in predictions)
    yield dg.AssetCheckResult(
        check_name="check_prediction_format",
        passed=valid_predictions,
        asset_key="batch_digit_predictions",
        metadata={
            "num_predictions": len(predictions),
            "prediction_range": f"[{min(predictions)}, {max(predictions)}]"
            if predictions
            else "[]",
            "all_valid": valid_predictions,
        },
    )

    # Check confidence scores
    valid_confidences = all(0 <= conf <= 1 for conf in confidences)
    yield dg.AssetCheckResult(
        check_name="check_confidence_scores",
        passed=valid_confidences,
        asset_key="batch_digit_predictions",
        metadata={
            "num_confidences": len(confidences),
            "confidence_range": f"[{min(confidences):.3f}, {max(confidences):.3f}]"
            if confidences
            else "[]",
            "all_valid": valid_confidences,
        },
    )
