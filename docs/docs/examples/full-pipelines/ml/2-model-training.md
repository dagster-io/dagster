---
title: Build and train the CNN model
description: Build and train convolutional neural networks with configurable parameters
last_update:
  author: Dennis Hume
sidebar_position: 30
---

Training effective neural networks requires careful architecture design, configurable hyperparameters, and robust training loops. Our CNN implementation uses modern best practices including batch normalization, dropout regularization, and adaptive learning rate scheduling to achieve reliable digit classification performance.

## Configurable model architecture

The `DigitCNN` class implements a three-layer convolutional neural network designed specifically for MNIST's 28x28 grayscale images. The architecture follows the principle of progressive feature abstraction—early layers detect edges and simple patterns, while deeper layers combine these into complex shapes for final classification:

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/model_assets.py"
  language="python"
  startAfter="start_cnn_architecture"
  endBefore="end_cnn_architecture"
  title="src/project_ml/defs/assets/model_assets.py"
/>

The architecture demonstrates key design principles: progressive downsampling reduces spatial dimensions while increasing feature depth (28×28 → 14×14 → 7×7 → 3×3), batch normalization after each convolution stabilizes training and enables higher learning rates, and strategic dropout prevents overfitting on spatial patterns. The configurable design allows easy experimentation with different channel sizes, dropout rates, and architectural components through the ModelConfig system.

## Training configuration system

Rather than hardcoding training parameters, the system uses Dagster's configuration framework to enable experimentation without code modifications. The `ModelConfig` class centralizes all training hyperparameters, from model architecture to optimization strategies:

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/model_assets.py"
  language="python"
  startAfter="start_model_config"
  endBefore="end_model_config"
  title="src/project_ml/defs/assets/model_assets.py"
/>

This configuration approach separates model architecture from training strategy, enabling data scientists to experiment with different hyperparameters through configuration files while keeping the underlying training logic stable. The configuration includes advanced features like learning rate scheduling (StepLR), early stopping with patience, multiple optimizer support, and automatic model persistence with descriptive filenames.

## Training asset orchestration

The `digit_classifier` asset coordinates the entire training process, from data loading through model persistence. This asset demonstrates how Dagster assets can orchestrate complex ML workflows while providing comprehensive logging and metadata generation:

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/model_assets.py"
  language="python"
  startAfter="start_training_asset"
  endBefore="end_training_asset"
  title="src/project_ml/defs/assets/model_assets.py"
/>

The training asset integrates seamlessly with upstream data processing through Dagster's dependency system, ensuring training only begins after data preprocessing completes. It accepts configuration parameters that control all aspects of training behavior, enabling different strategies across development and production environments. The asset generates rich metadata including training metrics, model statistics, and configuration parameters that appear in Dagster's UI for experiment tracking and comparison.

## Advanced training features and monitoring

The training system includes sophisticated features for production ML workflows: early stopping monitors validation accuracy and halts training when improvement stagnates (with configurable patience), learning rate scheduling reduces rates during plateaus for better convergence, and comprehensive logging tracks both epoch-level progress and batch-level details for debugging.

Multiple optimizer support (Adam for fast convergence, SGD with momentum for potentially better final performance) provides flexibility for different training scenarios. The system automatically handles GPU/CPU device selection and includes robust error handling for production deployment scenarios.

Model persistence uses descriptive filenames including timestamps and performance metrics, enabling easy model identification and version management. The integration with Dagster's resource system abstracts storage details, supporting both local development and cloud production environments seamlessly.

## Next steps

With trained models available through our asset pipeline, the next phase focuses on comprehensive evaluation to assess model performance and determine readiness for production deployment.

- Continue this tutorial with [model evaluation and deployment](/examples/full-pipelines/ml/evaluation-deployment)
