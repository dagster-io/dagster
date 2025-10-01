from typing import Any

import dagster as dg
import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset


# start_batch_prediction_config
class BatchPredictionConfig(dg.Config):
    """Configuration for batch prediction processing."""

    batch_size: int = 64
    num_test_images: int = 100  # Number of dummy images for demo
    confidence_threshold: float = 0.8  # Threshold for low confidence warning
    device: str = "cuda"  # Will fallback to CPU if CUDA not available


# end_batch_prediction_config


# start_realtime_prediction_config
class RealTimePredictionConfig(dg.Config):
    """Configuration for real-time prediction processing."""

    batch_size: int = 10  # Default number of images to process at once
    device: str = "cuda"  # Will fallback to CPU if CUDA not available
    confidence_threshold: float = 0.9  # Higher threshold for real-time predictions
    return_probabilities: bool = False  # Whether to return full probability distribution


# end_realtime_prediction_config


@dg.asset(
    description="Generate predictions on uploaded digit images",
    group_name="inference",
    required_resource_keys={"model_storage"},
    deps=["production_digit_classifier"],
)
def batch_digit_predictions(
    context,
    config: BatchPredictionConfig,
) -> dict[str, list]:
    """Process overnight batch of user-uploaded digit images."""
    # Get the model store resource
    model_store = context.resources.model_storage

    try:
        # List saved models and get the latest one
        saved_models = model_store.list_models()
        if not saved_models:
            context.log.error("No saved models found")
            return {"predictions": [], "confidences": []}

        # Get the latest model name (first one is newest due to sorting)
        latest_model_name = saved_models[0]  # Already just the model name
        context.log.info(f"Loading production model: {latest_model_name}")

        # Load the model using the resource
        model_data = model_store.load_model(latest_model_name)

        # Handle both formats: dict with 'model' key or direct model object
        if isinstance(model_data, dict) and "model" in model_data:
            production_model = model_data["model"]
        else:
            production_model = model_data  # Direct model object

        context.log.info("Model loaded successfully")
        context.log.info(f"Model architecture:\n{production_model!s}")

    except Exception as e:
        context.log.error(f"Failed to load production model: {e!s}")
        context.log.error(f"Exception details: {e.__class__.__name__!s}")
        import traceback

        context.log.error(f"Traceback: {traceback.format_exc()}")
        return {"predictions": [], "confidences": []}

    # For demo purposes, create some dummy test images
    dummy_images = torch.randn(config.num_test_images, 1, 28, 28)

    device = torch.device(
        config.device if torch.cuda.is_available() and config.device == "cuda" else "cpu"
    )
    production_model.to(device)
    production_model.eval()

    # Preprocess images
    processed_images = dummy_images.float() / 255.0

    dataset = TensorDataset(processed_images)
    dataloader = DataLoader(dataset, batch_size=config.batch_size, shuffle=False)

    predictions = []
    confidences = []

    with torch.no_grad():
        for (data,) in dataloader:
            _data = data.to(device)
            outputs = production_model(_data)
            probabilities = torch.softmax(outputs, dim=1)
            predicted_classes = torch.argmax(probabilities, dim=1)
            max_confidences = torch.max(probabilities, dim=1)[0]

            predictions.extend(predicted_classes.cpu().numpy().tolist())
            confidences.extend(max_confidences.cpu().numpy().tolist())

    context.add_output_metadata(
        {
            "total_predictions": len(predictions),
            "avg_confidence": float(np.mean(confidences)),
            "low_confidence_count": sum(1 for c in confidences if c < config.confidence_threshold),
            "confidence_threshold": config.confidence_threshold,
            "model_path": latest_model_name,
        },
        output_name="result",
    )

    context.log.info(f"Generated {len(predictions)} batch predictions")

    return {"predictions": predictions, "confidences": confidences}


@dg.asset(
    description="Real-time digit prediction endpoint",
    group_name="inference",
    required_resource_keys={"model_storage"},
    deps=["production_digit_classifier"],
)
def digit_predictions(
    context,
    config: RealTimePredictionConfig,
) -> dict[str, Any]:
    """Classify new handwritten digits in real-time."""
    # Get the model store resource
    model_store = context.resources.model_storage

    try:
        # List saved models and get the latest one
        saved_models = model_store.list_models()
        if not saved_models:
            context.log.error("No saved models found")
            return {
                "prediction": None,
                "confidence": 0.0,
                "error": "No models available",
            }

        # Get the latest model name (first one is newest due to sorting)
        latest_model_name = saved_models[0]  # Already just the model name
        context.log.info(f"Loading production model: {latest_model_name}")

        # Load the model using the resource
        model_data = model_store.load_model(latest_model_name)

        # Handle both formats: dict with 'model' key or direct model object
        if isinstance(model_data, dict) and "model" in model_data:
            production_model = model_data["model"]
        else:
            production_model = model_data  # Direct model object

        context.log.info("Model loaded successfully")

    except Exception as e:
        context.log.error(f"Failed to load production model: {e!s}")
        return {"prediction": None, "confidence": 0.0, "error": str(e)}

    # For demo purposes, create some test images
    input_images = torch.randn(config.batch_size, 1, 28, 28)

    device = torch.device(
        config.device if torch.cuda.is_available() and config.device == "cuda" else "cpu"
    )
    production_model.to(device)
    production_model.eval()

    # Preprocess input images
    processed_images = input_images.float() / 255.0

    predictions = []
    confidences = []
    all_probabilities = []

    with torch.no_grad():
        processed_images = processed_images.to(device)
        outputs = production_model(processed_images)
        probabilities = torch.softmax(outputs, dim=1)
        predicted_classes = torch.argmax(probabilities, dim=1)
        max_confidences = torch.max(probabilities, dim=1)[0]

        predictions = predicted_classes.cpu().numpy().tolist()
        confidences = max_confidences.cpu().numpy().tolist()

        if config.return_probabilities:
            all_probabilities = probabilities.cpu().numpy().tolist()

    avg_confidence = float(np.mean(confidences))
    context.add_output_metadata(
        {
            "prediction_count": len(predictions),
            "avg_confidence": avg_confidence,
            "high_confidence_predictions": sum(
                1 for c in confidences if c >= config.confidence_threshold
            ),
            "confidence_threshold": config.confidence_threshold,
            "model_path": latest_model_name,
        },
        output_name="result",
    )

    result = {
        "predictions": predictions,
        "confidences": confidences,
    }

    if config.return_probabilities:
        result["probabilities"] = all_probabilities

    if avg_confidence < config.confidence_threshold:
        context.log.warning(
            f"Average confidence {avg_confidence:.2f} below threshold {config.confidence_threshold}"
        )

    return result
