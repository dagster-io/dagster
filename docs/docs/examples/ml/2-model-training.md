---
title: CNN model training
description: Build and train convolutional neural networks for digit classification
last_update:
  author: Dennis Hume
sidebar_position: 30
---

# CNN model training

Building an effective digit classifier requires thoughtful architecture design and training strategies that balance model expressiveness with generalization. This section explores how to implement configurable CNN training that adapts to different requirements while maintaining production-ready practices.

## CNN architecture design

Our three-layer CNN architecture embodies the principle of progressive feature abstraction, transforming raw 28x28 pixel grids into increasingly abstract representations that capture the essence of handwritten digits. The design follows proven computer vision principles: early layers detect edges and simple patterns, middle layers combine these into complex shapes, and final layers integrate features for classification decisions.

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/model_assets.py"
  language="python"
  startAfter="start_cnn_architecture"
  endBefore="end_cnn_architecture"
  title="Three-layer CNN with progressive feature extraction"
/>

The architecture demonstrates several key design principles within our ML pipeline:

**Progressive downsampling**: Each convolutional layer reduces spatial dimensions while increasing feature depth (28×28 → 14×14 → 7×7 → 3×3), concentrating spatial information into increasingly rich feature representations.

**Batch normalization placement**: Applied after each convolution but before activation, batch normalization stabilizes training by normalizing layer inputs, enabling higher learning rates and reducing sensitivity to weight initialization.

**Strategic dropout application**: 2D spatial dropout after the second convolution prevents overfitting on spatial patterns, while standard dropout in fully connected layers regularizes final classification features.

**Adaptive pooling**: The final layer uses adaptive average pooling to ensure consistent output dimensions, making the architecture robust to input size variations.

## Configuration-driven training

Rather than hardcoding training parameters, the system uses Dagster's configuration framework to enable experimentation without code modifications. This approach separates model architecture from training strategy, enabling data scientists to experiment through configuration files while keeping the underlying training logic stable.

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/model_assets.py"
  language="python"
  startAfter="start_model_config"
  endBefore="end_model_config"
  title="Comprehensive training configuration"
/>

This configuration approach serves several purposes in our pipeline:

**Environment flexibility**: Production deployments can use different configurations for different environments without code changes—development might use fewer epochs and lower thresholds for rapid iteration, while production uses comprehensive training with strict quality criteria.

**Experiment tracking**: Different training runs can be easily compared by varying configuration parameters, with all settings automatically captured in the asset metadata for full reproducibility.

**Advanced training features**: The configuration includes learning rate scheduling (StepLR reducing rates by 90% every 10 epochs), early stopping with patience (waiting 7 epochs for improvement), and multiple optimizer support (Adam for fast convergence, SGD with momentum for potentially better final performance).

**Model persistence**: Automatic model saving with descriptive filenames including timestamps and performance metrics enables easy model identification and version management.

## Training asset implementation

The training pipeline coordinates data loading, model initialization, training loops, and model persistence through a single Dagster asset that demonstrates production best practices.

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/model_assets.py"
  language="python"
  startAfter="start_training_asset"
  endBefore="end_training_asset"
  title="Complete training asset with monitoring"
/>

This training asset showcases several critical concepts for production ML systems:

**Asset dependencies**: The asset depends on processed_mnist_data, ensuring training only begins after data preprocessing completes. Dagster's dependency system manages execution order automatically.

**Configuration integration**: The asset accepts a ModelConfig parameter that controls all aspects of training behavior, enabling different training strategies across environments without code changes.

**Comprehensive logging**: Detailed progress tracking at both epoch and batch levels enables monitoring training health and debugging convergence issues. All metrics are logged through Dagster's context system.

**Rich metadata generation**: Training results include model statistics, configuration parameters, and performance metrics that appear in Dagster's UI, enabling easy comparison between different training runs and full experiment reproducibility.

**Resource integration**: The asset uses the model_storage resource for persistence, abstracting storage details and enabling seamless transitions between local development and cloud production environments.

## Production training considerations

Production ML systems require robust monitoring and best practices to ensure reliable model training at scale:

**Training monitoring**: Track loss trajectories (both training and validation should decrease over time), learning rate effectiveness (smooth loss decreases indicate good rates), and hardware utilization (GPU utilization should remain high with memory usage below limits).

**Hyperparameter guidelines**: Start with batch sizes of 32-64 for good gradient estimates, learning rates of 0.001 for Adam optimizer, and early stopping patience of 5-10 epochs to balance thoroughness with efficiency.

**Integration patterns**: The training asset integrates seamlessly with upstream data processing and downstream evaluation components through Dagster's dependency system, while generated metadata enables deployment decisions based on training performance.

**Scalability considerations**: For larger models or datasets, consider distributed training, gradient checkpointing for memory efficiency, and mixed-precision training for faster convergence while maintaining numerical stability.

The configuration-driven approach ensures that these production practices can be applied consistently across different environments while maintaining the flexibility needed for experimentation and optimization.

## Next steps

With trained models available, the next phase focuses on comprehensive evaluation to understand model performance, identify potential issues, and determine readiness for production deployment.

- Continue this tutorial with [model evaluation](/examples/ml/model-evaluation)
