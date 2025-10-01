---
title: Model evaluation and metrics
description: Assess trained model performance with comprehensive testing and analysis
last_update:
  author: Dennis Hume
sidebar_position: 40
---

# Model evaluation and metrics

Thorough model evaluation forms the cornerstone of reliable machine learning systems. Beyond simple accuracy metrics, comprehensive evaluation reveals model behavior patterns, identifies potential failure modes, and provides the evidence needed for confident production deployment decisions.

## Comprehensive model evaluation

The evaluation asset provides multi-metric assessment using the held-out test set that was never seen during training or validation. This honest evaluation is crucial for making informed deployment decisions and understanding real-world model performance.

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/model_assets.py"
  language="python"
  startAfter="start_model_evaluation"
  endBefore="end_model_evaluation"
  title="Multi-metric evaluation with robust error handling"
/>

This evaluation asset demonstrates several key concepts within our ML pipeline:

**Model loading and versioning**: The asset automatically loads the most recently trained model from the model storage system, ensuring evaluation always reflects the latest training results without manual intervention.

**Multi-metric analysis**: Beyond simple accuracy, the evaluation calculates precision, recall, and F1-scores for each digit class, providing a comprehensive view of model performance across all classification scenarios.

**Confusion matrix generation**: Creates detailed confusion matrices that reveal systematic error patterns—which digits are frequently confused and whether errors follow logical patterns (visually similar digits) or indicate fundamental training issues.

**Robust error handling**: Comprehensive error handling provides detailed debugging information when model loading fails while returning safe default values that won't break downstream pipeline components.

**Rich metadata generation**: All evaluation results are captured as metadata that appears in Dagster's UI, enabling performance tracking, model comparison, and quality monitoring across different training runs.

## Understanding evaluation metrics

Machine learning evaluation extends far beyond single accuracy numbers, with different metrics revealing different aspects of model behavior:

**Overall accuracy**: The percentage of correctly classified test images provides a high-level performance indicator. For digit classification, accuracy above 95% typically indicates production readiness, while accuracy below 90% suggests architectural or training issues.

**Precision and recall analysis**: Per-class precision reveals how often the model's digit predictions are correct, while recall shows how well the model identifies each digit type. These metrics often reveal patterns—some digits like '1' are easier to identify accurately, while others like '8' vs '3' present consistent challenges.

**Macro-averaged metrics**: Standard accuracy can be misleading when some digit classes are easier to classify than others. Macro-averaging treats all classes equally, preventing performance inflation from easy-to-classify digits and providing balanced performance assessment.

**Confusion matrix insights**: Common confusion patterns in digit classification include '4' and '9' (similar stroke patterns), '3' and '8' (curved elements), '6' and '0' (circular shapes), and '1' and '7' (simple vertical strokes). Understanding these patterns helps evaluate whether model errors make intuitive sense or suggest deeper problems.

## Performance benchmarking and quality gates

The evaluation system provides context for deployment decisions through well-established performance benchmarks and configurable quality thresholds:

**MNIST benchmarks**: Baseline threshold of 90% accuracy indicates basic model competency, 95%+ accuracy suggests production readiness, and modern CNNs routinely achieve 99%+ accuracy. Understanding where model performance sits relative to these benchmarks informs decisions about training, architecture changes, or deployment.

**Configurable thresholds**: Different deployment scenarios require different evaluation criteria—development environments might accept lower accuracy thresholds for rapid experimentation, while production systems demand higher performance standards. The configuration system enables environment-specific criteria without code changes.

**Automated deployment integration**: Evaluation results feed directly into deployment pipelines, enabling quality gates that prevent low-performing models from reaching production. Only models meeting predefined performance criteria are deployed automatically, with comprehensive metadata supporting deployment decision-making.

**Test set integrity**: Evaluation always uses the original MNIST test set that was never seen during training or validation, ensuring results reflect true generalization performance rather than memorization of training patterns.

## Production evaluation considerations

Production ML systems require robust evaluation practices that ensure reliable model assessment at scale:

**Monitoring and observability**: Production evaluation generates metadata that enables performance tracking across different training runs, model lineage linking results to specific trained models, quality monitoring with alerts for underperforming models, and trend analysis tracking performance changes over time.

**Evaluation best practices**: Process test images in configurable batches to balance memory usage with processing efficiency, consider multiple evaluation runs with different random seeds for critical deployment decisions to understand performance variance, and implement evaluation checkpointing for larger datasets to handle interruptions gracefully.

**Beyond basic metrics**: Comprehensive evaluation includes confidence analysis to identify uncertain predictions needing human review, error pattern analysis to reveal data quality issues or architectural improvements, and robustness testing on modified inputs (rotations, noise) to assess model stability for production deployment.

**Integration patterns**: The evaluation asset integrates seamlessly with both upstream training components and downstream deployment systems through Dagster's dependency management, while rich metadata enables automated deployment decisions and comprehensive experiment tracking.

## Next steps

With comprehensive evaluation metrics providing confidence in model performance, the final step involves deploying high-quality models to production and establishing inference endpoints for serving predictions.

- Continue this tutorial with [deployment and inference](/examples/ml/deployment-inference)
