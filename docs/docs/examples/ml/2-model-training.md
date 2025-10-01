---
title: CNN model training
description: Build and train convolutional neural networks for digit classification
last_update:
  author: Dennis Hume
sidebar_position: 30
---

# CNN model training

Building an effective digit classifier requires thoughtful architecture design and training strategies that balance model expressiveness with generalization. This section explores how to implement configurable CNN training that adapts to different requirements while maintaining production-ready practices.

## Architecture philosophy

Modern convolutional neural networks succeed through progressive feature abstraction. Our three-layer CNN architecture embodies this principle, transforming raw 28x28 pixel grids into increasingly abstract representations that capture the essence of handwritten digits.

The design follows proven computer vision principles: early layers detect edges and simple patterns, middle layers combine these into more complex shapes, and final layers integrate these features for classification decisions. This hierarchical approach mirrors how human visual systems process images.

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/model_assets.py"
  language="python"
  startAfter="start_cnn_architecture"
  endBefore="end_cnn_architecture"
  title="Three-layer CNN with progressive feature extraction"
/>

## Key architectural decisions

**Progressive downsampling**: Each convolutional layer reduces spatial dimensions while increasing feature depth (28×28 → 14×14 → 7×7 → 3×3). This pattern concentrates spatial information into increasingly rich feature representations.

**Batch normalization placement**: Applied after each convolution but before activation, batch normalization stabilizes training by normalizing layer inputs. This enables higher learning rates and reduces sensitivity to weight initialization.

**Strategic dropout application**: 2D spatial dropout after the second convolution prevents overfitting on spatial patterns, while standard dropout in fully connected layers regularizes final classification features.

**Adaptive pooling**: The final layer uses adaptive average pooling to ensure consistent output dimensions, making the architecture robust to input size variations.

## Configuration-driven training

Rather than hardcoding training parameters, the system uses Dagster's configuration framework to enable experimentation without code modifications.

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/model_assets.py"
  language="python"
  startAfter="start_model_config"
  endBefore="end_model_config"
  title="Comprehensive training configuration"
/>

This configuration approach separates concerns between model architecture and training strategy. Data scientists can experiment with different hyperparameters through configuration files, while the underlying training logic remains stable. Production deployments can use different configurations for different environments without code changes.

## Advanced training strategies

### Learning rate scheduling

Effective neural network training requires careful learning rate management. Static learning rates often lead to suboptimal convergence - too high and training becomes unstable, too low and convergence is unnecessarily slow.

The StepLR scheduler reduces learning rates during training plateaus, typically by 90% every 10 epochs. This allows initial rapid learning with higher rates, then fine-tuning with reduced rates as the model approaches optimal parameter values.

### Early stopping with patience

Overfitting represents a fundamental challenge in machine learning - models that perform well on training data but poorly on new examples. Early stopping addresses this by monitoring validation performance and halting training when improvement stagnates.

The patience mechanism waits for several epochs without improvement before stopping, balancing thoroughness with efficiency. Seven epochs of patience provides sufficient opportunity for temporary validation plateaus while preventing excessive training on overfit models.

### Optimizer selection and tuning

Different optimization algorithms offer distinct advantages for neural network training. Adam combines momentum with adaptive learning rates, making it effective for computer vision tasks with minimal tuning. SGD with momentum can achieve better final performance but requires more careful learning rate selection.

The configuration system enables easy optimizer experimentation, supporting both Adam and SGD with momentum. Weight decay provides L2 regularization that prevents parameter values from growing excessively large.

## Training asset orchestration

The training pipeline coordinates data loading, model initialization, training loops, and model persistence through a single Dagster asset.

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/model_assets.py"
  language="python"
  startAfter="start_training_asset"
  endBefore="end_training_asset"
  title="Training asset with comprehensive logging and metadata"
/>

This asset demonstrates several production best practices:

**Comprehensive logging**: Detailed progress tracking enables monitoring training health and debugging convergence issues. Epoch-level summaries provide high-level progress while batch-level logging helps identify training instabilities.

**Rich metadata generation**: Training results include model statistics, configuration parameters, and performance metrics that appear in Dagster's UI. This metadata enables easy comparison between different training runs.

**Automatic model persistence**: Trained models are saved with descriptive filenames including timestamps and performance metrics, enabling easy model identification and version management.

## Training monitoring and debugging

Production ML systems require robust monitoring to identify training issues early. Key metrics to track include:

**Loss trajectories**: Both training and validation loss should decrease over time. Diverging losses indicate overfitting, while oscillating losses suggest learning rates that are too high.

**Learning rate effectiveness**: Monitoring how learning rate changes affect convergence helps optimize training schedules. Effective rates show smooth loss decreases, while ineffective rates show minimal progress.

**Memory and compute utilization**: Training efficiency depends on effective hardware utilization. GPU utilization should remain high during training phases, with memory usage staying below hardware limits.

## Configuration best practices

Successful training requires balancing multiple competing objectives through careful hyperparameter selection:

**Batch size selection**: Smaller batches (32-64) provide noisier but potentially better gradient estimates, while larger batches offer more stable training at the cost of increased memory requirements.

**Learning rate tuning**: Start with 0.001 for Adam optimizer and adjust based on loss trajectory behavior. Learning rates that are too high cause training instability, while rates that are too low result in unnecessarily slow convergence.

**Early stopping tuning**: Patience between 5-10 epochs works well for most computer vision tasks. Shorter patience may halt training prematurely during temporary plateaus, while longer patience wastes computational resources on overfit models.

## Integration with broader ML workflow

The training asset integrates seamlessly with upstream data processing and downstream evaluation components. Dagster's dependency system ensures training only begins after data preprocessing completes, while generated metadata enables downstream components to access model performance information for deployment decisions.

## Next steps

With trained models available, the next phase focuses on comprehensive evaluation to understand model performance, identify potential issues, and determine readiness for production deployment.

- Continue this tutorial with [model evaluation](/examples/ml/model-evaluation)
