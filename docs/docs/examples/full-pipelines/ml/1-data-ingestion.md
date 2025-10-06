---
title: Ingest and preprocess data
description: Download and prepare MNIST data for model training
last_update:
  author: Dennis Hume
sidebar_position: 20
---

The foundation of reliable ML systems starts with clean, well-structured data pipelines. Our data ingestion system automates [MNIST dataset](https://en.wikipedia.org/wiki/MNIST_database) downloading, applies proper preprocessing transforms, and creates stratified train/validation splits that ensure honest model evaluation.

## Automated data downloading with normalization

The `raw_mnist_data` asset handles the critical first step of our pipeline—downloading and normalizing the MNIST dataset automatically. Rather than requiring manual data management, this asset leverages PyTorch's built-in dataset utilities to handle downloading, caching, and initial preprocessing:

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/data_assets.py"
  language="python"
  startAfter="start_raw_data_loading"
  endBefore="end_raw_data_loading"
  title="src/project_ml/defs/assets/data_assets.py"
/>

The normalization transforms applied during data loading use MNIST's precomputed statistics (mean=0.1307, std=0.3081) to standardize pixel values across the entire dataset. This preprocessing is crucial for neural network training stability, it prevents certain neurons from dominating due to input scale differences and enables faster convergence. The asset returns structured tensors that downstream assets can depend on, creating clear data lineage in Dagster's dependency graph.

## Strategic training and validation splitting

The `processed_mnist_data` asset implements stratified validation splitting that maintains class balance while creating proper boundaries between training and validation data. This separation is essential for honest performance estimation during model development:

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/data_assets.py"
  language="python"
  startAfter="start_data_preprocessing"
  endBefore="end_data_preprocessing"
  title="src/project_ml/defs/assets/data_assets.py"
/>

Stratified splitting ensures each digit class (0-9) appears proportionally in both training and validation sets, preventing validation bias that could occur with random splits. The 20% validation split provides sufficient data for reliable performance monitoring while preserving most training data. The asset generates comprehensive metadata about dataset sizes, image dimensions, and class distributions that appears in Dagster's UI for immediate data quality visibility.

## Configuration and reproducibility management

The data pipeline uses centralized constants to control critical parameters like validation split ratios and random seeds. This approach ensures reproducible experiments across different environments while enabling easy adjustment of preprocessing strategies:

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/constants.py"
  language="python"
  startAfter="# Data Processing"
  endBefore="# MNIST Constants"
  title="src/project_ml/defs/constants.py"
/>

These constants integrate seamlessly with Dagster's configuration system, allowing different environments to use different preprocessing strategies without code changes. The random seed ensures reproducible data splits for consistent experimentation, while the validation split ratio can be adjusted based on dataset size and modeling requirements.

## Asset dependency and metadata tracking

Dagster automatically tracks the relationship between raw and processed data assets, creating clear lineage from downloads through final processed tensors. Each asset generates rich metadata that enables data quality monitoring and pipeline debugging:

The asset system provides automatic lineage tracking from raw downloads through processed data, enabling full reproducibility of any downstream model results. Metadata including dataset statistics, processing parameters, and data quality metrics appears in Dagster's UI, providing immediate visibility into pipeline health and enabling rapid debugging when issues arise.

This asset-based approach scales naturally to production scenarios where data processing might involve multiple transformation steps, external data sources, or complex validation requirements while maintaining the same clear dependency structure and comprehensive observability.

## Next steps

With clean, preprocessed data available through our asset pipeline, we can move to model training where we'll build and optimize a CNN classifier using this structured data foundation.

- Continue this tutorial with [model training](/examples/full-pipelines/ml/model-training)
