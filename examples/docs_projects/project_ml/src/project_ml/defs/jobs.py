import dagster as dg

from project_ml.defs.assets import (
    batch_digit_predictions,
    digit_classifier,
    model_evaluation,
    processed_mnist_data,
    production_digit_classifier,
    raw_mnist_data,
)

training_job = dg.define_asset_job(
    name="digit_classifier_training",
    selection=[
        raw_mnist_data,
        processed_mnist_data,
        digit_classifier,
        model_evaluation,
    ],
    description="Train and evaluate digit classification model",
)

deployment_job = dg.define_asset_job(
    name="model_deployment",
    selection=[production_digit_classifier],
    description="Deploy model to production if quality threshold is met",
)

inference_job = dg.define_asset_job(
    name="batch_inference",
    selection=[batch_digit_predictions],
    description="Run batch predictions on uploaded images",
)

full_pipeline_job = dg.define_asset_job(
    name="full_ml_pipeline",
    selection="*",
    description="Complete ML pipeline from data to deployment",
)
