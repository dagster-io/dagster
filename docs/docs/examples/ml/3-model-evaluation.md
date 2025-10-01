---
title: Model evaluation and metrics
description: Assess trained model performance with comprehensive testing and analysis
last_update:
  author: Dennis Hume
sidebar_position: 40
---

# Model evaluation and metrics

Thorough model evaluation forms the cornerstone of reliable machine learning systems. Beyond simple accuracy metrics, comprehensive evaluation reveals model behavior patterns, identifies potential failure modes, and provides the evidence needed for confident production deployment decisions.

## Evaluation philosophy

Effective model evaluation requires testing on data that was never seen during training or validation. The held-out test set provides the most honest assessment of how the model will perform on real-world inputs. This evaluation honesty is crucial for making informed deployment decisions.

## Comprehensive performance assessment

Machine learning evaluation extends far beyond single accuracy numbers. Different metrics reveal different aspects of model behavior, and understanding these nuances enables more informed model selection and deployment strategies.

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/model_assets.py"
  language="python"
  startAfter="start_model_evaluation"
  endBefore="end_model_evaluation"
  title="Multi-metric evaluation with error handling"
/>

## Understanding classification metrics

### Overall accuracy

The percentage of correctly classified test images provides a high-level performance indicator. For digit classification, accuracy above 95% typically indicates a model ready for production consideration, while accuracy below 90% suggests architectural or training issues that need addressing.

### Precision and recall analysis

Per-class precision reveals how often the model's digit predictions are correct, while recall shows how well the model identifies each digit type. These metrics often reveal interesting patterns - some digits (like '1') are easier to identify accurately, while others (like '8' vs '3') present consistent challenges.

### F1-score balance

The harmonic mean of precision and recall, F1-scores provide a balanced view of model performance that doesn't favor either metric. This balance is particularly important when different types of classification errors have different real-world costs.

## Confusion matrix insights

Confusion matrices reveal systematic error patterns that accuracy alone cannot capture. Understanding which digits are frequently confused helps identify whether model errors follow logical patterns (visually similar digits) or indicate more fundamental training issues.

Common confusion patterns in digit classification include:

- **'4' and '9'**: Similar stroke patterns can confuse models
- **'3' and '8'**: Curved elements create visual ambiguity
- **'6' and '0'**: Circular shapes with varying openings
- **'1' and '7'**: Simple vertical strokes with minimal distinguishing features

These patterns help evaluate whether model errors make intuitive sense or suggest deeper architectural problems.

## Macro-averaged metrics

Standard accuracy metrics can be misleading when some digit classes are easier to classify than others. Macro-averaging treats all classes equally, preventing performance inflation from easy-to-classify digits and providing a more balanced view of model capabilities.

This balanced perspective is crucial for applications where all digit classes matter equally. A model that achieves 98% accuracy by correctly classifying common digits while failing on rarer ones may not be suitable for applications requiring consistent performance across all digits.

## Robust error handling

Production evaluation systems must handle model loading failures, missing files, and unexpected data formats gracefully. The evaluation asset includes comprehensive error handling that provides detailed debugging information while returning safe default values that won't break downstream pipeline components.

This resilience is essential for production systems where evaluation may run automatically as part of deployment pipelines. Failed evaluations should provide clear error messages for debugging while not preventing other pipeline components from functioning.

## Performance benchmarking context

MNIST digit classification has well-established performance benchmarks that provide context for evaluation results:

- **Baseline threshold**: 90% accuracy indicates basic model competency
- **Production readiness**: 95%+ accuracy suggests deployment consideration
- **State-of-the-art**: Modern CNNs routinely achieve 99%+ accuracy

Understanding where model performance sits relative to these benchmarks helps make informed decisions about whether additional training, architectural changes, or deployment are appropriate.

## Evaluation configuration and flexibility

Different deployment scenarios may require different evaluation criteria. Development environments might accept lower accuracy thresholds for rapid experimentation, while production systems demand higher performance standards.

The configuration system enables environment-specific evaluation criteria without code changes, supporting different accuracy thresholds, batch sizes, and evaluation strategies across development, staging, and production environments.

## Integration with deployment decisions

Evaluation results feed directly into automated deployment pipelines, enabling quality gates that prevent low-performing models from reaching production. This integration ensures that only models meeting predefined performance criteria are deployed automatically.

The metadata generated during evaluation provides rich information for deployment decision-making, including not just accuracy numbers but also confidence distributions, error patterns, and model lineage information.

## Monitoring and observability

Production evaluation generates metadata that appears in Dagster's asset materialization views, enabling:

- **Performance tracking**: Compare metrics across different training runs and model versions
- **Model lineage**: Link evaluation results to specific trained models and training configurations
- **Quality monitoring**: Set up alerts for models that fall below performance thresholds
- **Trend analysis**: Track how model performance changes over time as training strategies evolve

## Evaluation best practices

### Test set integrity

The evaluation always uses the original MNIST test set that was never seen during training or validation. This separation ensures evaluation results reflect true generalization performance rather than memorization of training patterns.

### Batch processing efficiency

Evaluation processes test images in configurable batches, balancing memory usage with processing efficiency. For larger datasets, consider implementing evaluation checkpointing to handle interruptions gracefully and resume from partial progress.

### Statistical significance

Single evaluation runs can be influenced by random factors in model initialization or data ordering. For critical deployment decisions, consider multiple evaluation runs with different random seeds to understand performance variance.

## Beyond basic metrics

Comprehensive evaluation extends beyond standard classification metrics to include:

**Confidence analysis**: Understanding how confident the model is in its predictions helps identify uncertain cases that might need human review.

**Error pattern analysis**: Systematic analysis of misclassified examples can reveal data quality issues or suggest architectural improvements.

**Robustness testing**: Evaluating performance on slightly modified inputs (rotations, noise) reveals model stability characteristics important for production deployment.

## Next steps

With comprehensive evaluation metrics providing confidence in model performance, the final step involves deploying high-quality models to production and establishing inference endpoints for serving predictions.

- Continue this tutorial with [deployment and inference](/examples/ml/deployment-inference)
