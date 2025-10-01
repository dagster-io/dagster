---
title: MNIST data ingestion
description: Download and preprocess handwritten digit images for ML training
last_update:
  author: Dennis Hume
sidebar_position: 20
---

# MNIST data ingestion

The foundation of any successful machine learning pipeline is clean, well-structured data. This section demonstrates how to build robust data ingestion assets that download, preprocess, and prepare the MNIST handwritten digit dataset for neural network training.

## Dataset overview and significance

The MNIST dataset serves as the "Hello World" of computer vision, containing 70,000 grayscale images of handwritten digits (0-9). Each 28x28 pixel image represents a real-world data engineering challenge: consistent preprocessing, proper normalization, and strategic data splitting for reliable model validation.

## Raw data loading strategy

The first asset in our pipeline handles the critical task of downloading and initial preprocessing. Rather than relying on manual data management, this asset automates the entire process from download to tensor conversion.

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/data_assets.py"
  language="python"
  startAfter="start_raw_data_loading"
  endBefore="end_raw_data_loading"
  title="Data loading with automatic normalization"
/>

The key insight here is applying normalization at the data loading stage. Using MNIST's precomputed statistics (mean=0.1307, std=0.3081) ensures that pixel values are standardized across the entire dataset. This preprocessing step is crucial for neural network training stability - it prevents certain neurons from dominating due to input scale differences and enables faster convergence.

## Strategic data splitting for reliable validation

Machine learning models require careful data partitioning to provide honest performance estimates. The preprocessing asset implements stratified validation splitting that maintains class balance while creating proper train/validation boundaries.

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/data_assets.py"
  language="python"
  startAfter="start_data_preprocessing"
  endBefore="end_data_preprocessing"
  title="Stratified validation split with metadata tracking"
/>

## Why stratified splitting matters

Standard random splits can create validation sets that don't represent the true class distribution. For digit classification, this could mean a validation set with too few examples of certain digits, leading to misleading performance metrics. Stratified splitting ensures each digit class appears proportionally in both training and validation sets.

The 20% validation split strikes a balance between having enough data for training and sufficient samples for reliable validation metrics. This ratio has proven effective across many computer vision tasks.

## Metadata-driven data quality

Each asset generates comprehensive metadata that enables data quality monitoring and pipeline debugging. The system tracks dataset sizes, image dimensions, class counts, and distribution statistics. This metadata appears in Dagster's UI, providing immediate visibility into data pipeline health and enabling rapid debugging when issues arise.

## Configuration and reproducibility

The data processing pipeline uses centralized constants for critical parameters like validation split ratios and random seeds. This approach ensures reproducible experiments while enabling easy adjustment of preprocessing strategies across different environments.

## Production considerations

For larger datasets beyond MNIST's modest size, the in-memory tensor approach would need modification. Production systems typically implement:

- **Streaming data loaders** that process batches on-demand to manage memory usage
- **Data asset partitioning** to handle subsets independently and enable parallel processing
- **External storage references** using URIs rather than materializing large tensors in memory

The current implementation prioritizes simplicity and fast iteration for the tutorial context, but the patterns extend naturally to production-scale data volumes.

## Data lineage and traceability

Dagster's asset system automatically tracks data lineage from raw downloads through processed tensors. This lineage enables understanding exactly how any downstream model result traces back to specific data processing decisions, crucial for debugging model performance issues or reproducing experimental results.

## Next steps

With clean, well-structured data assets providing reliable train/validation/test splits, the next phase focuses on building and training the CNN architecture that will learn to classify these handwritten digits.

- Continue this tutorial with [model training](/examples/ml/model-training)
