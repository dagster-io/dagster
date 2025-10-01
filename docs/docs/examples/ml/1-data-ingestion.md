---
title: MNIST data ingestion
description: Download and preprocess handwritten digit images for ML training
last_update:
  author: Dennis Hume
sidebar_position: 20
---

# MNIST data ingestion

The foundation of any successful machine learning pipeline is clean, well-structured data. This section demonstrates how to build robust data ingestion assets that download, preprocess, and prepare the MNIST handwritten digit dataset for neural network training.

## Automated data loading with normalization

The first asset in our pipeline handles the critical task of downloading and initial preprocessing. Rather than relying on manual data management, this asset automates the entire process from download to tensor conversion with proper normalization.

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/data_assets.py"
  language="python"
  startAfter="start_raw_data_loading"
  endBefore="end_raw_data_loading"
  title="Automated MNIST download with normalization"
/>

This asset demonstrates several key concepts in the context of our ML pipeline:

- **Automatic dataset downloading**: The torchvision datasets module handles MNIST download and caching automatically
- **Preprocessing at load time**: Normalization transforms are applied during data loading using MNIST's precomputed statistics (mean=0.1307, std=0.3081)
- **Tensor conversion**: Raw PyTorch dataset objects are converted to tensors for efficient downstream processing
- **Asset return structure**: The asset returns a structured dictionary that downstream assets can depend on

The normalization step is crucial for neural network training stability—it prevents certain neurons from dominating due to input scale differences and enables faster convergence.

## Train/validation splitting with stratification

Machine learning models require careful data partitioning to provide honest performance estimates. This asset implements stratified validation splitting that maintains class balance while creating proper train/validation boundaries.

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/data_assets.py"
  language="python"
  startAfter="start_data_preprocessing"
  endBefore="end_data_preprocessing"
  title="Stratified data splitting with metadata"
/>

This preprocessing asset showcases important data engineering practices:

- **Stratified splitting**: Uses sklearn's train_test_split with stratification to ensure each digit class appears proportionally in both training and validation sets
- **Configurable parameters**: The validation split ratio (20%) and random seed are controlled through centralized constants for reproducibility
- **Rich metadata generation**: The asset produces comprehensive metadata about dataset sizes, image shapes, and class counts that appears in Dagster's UI
- **Asset dependencies**: The asset depends on the raw_mnist_data asset, creating clear data lineage

Standard random splits can create validation sets that don't represent the true class distribution, potentially leading to misleading performance metrics. Stratified splitting prevents this issue.

## Data quality monitoring and lineage

Dagster's asset system automatically provides comprehensive data quality monitoring and lineage tracking throughout the ingestion pipeline. Each asset generates rich metadata that enables debugging and quality assurance:

**Metadata tracking**: Dataset sizes, image dimensions, class distributions, and processing statistics are automatically captured and displayed in the Dagster UI.

**Automatic lineage**: Dagster tracks how processed data assets trace back to raw downloads, enabling full reproducibility and debugging of data quality issues.

**Configuration management**: Critical parameters like validation split ratios and random seeds are managed through centralized constants, ensuring consistent behavior across environments while enabling easy experimentation.

**Asset dependencies**: Clear dependency relationships between raw and processed data assets create predictable execution order and enable selective recomputation when needed.

## Production scaling considerations

While this tutorial uses in-memory processing suitable for MNIST's modest size, production systems often require different approaches for larger datasets:

**Streaming data loaders**: For datasets that don't fit in memory, implement data loaders that process batches on-demand rather than loading entire datasets.

**Asset partitioning**: Dagster's partitioning system enables processing large datasets in chunks, supporting parallel execution and selective recomputation.

**External storage**: Production systems often store processed data in external systems (databases, cloud storage) rather than passing large tensors between assets.

**Data validation**: Implement additional data quality checks using tools like Great Expectations to validate data schema, value ranges, and statistical properties.

The patterns demonstrated here extend naturally to production-scale data volumes while maintaining the same clear asset structure and dependency management.

## Next steps

With clean, well-structured data assets providing reliable train/validation/test splits, the next phase focuses on building and training the CNN architecture that will learn to classify these handwritten digits.

- Continue this tutorial with [model training](/examples/ml/model-training)
