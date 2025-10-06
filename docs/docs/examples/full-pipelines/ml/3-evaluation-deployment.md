---
title: Evaluate model performance and deploy to production
description: Assess model performance and deploy to production with quality gates
last_update:
  author: Dennis Hume
sidebar_position: 40
---

Reliable ML systems require comprehensive model evaluation and flexible deployment strategies. Our evaluation system generates detailed performance metrics and confusion matrix analysis, while the deployment pipeline supports multiple strategies from automatic quality based deployment to manual model selection.

## Comprehensive model evaluation

The `model_evaluation` asset provides multi-metric assessment using the held out test set that was never seen during training. This evaluation goes beyond simple accuracy to provide detailed insights into model behavior across all digit classes:

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/model_assets.py"
  language="python"
  startAfter="start_model_evaluation"
  endBefore="end_model_evaluation"
  title="src/project_ml/defs/assets/model_assets.py"
/>

The evaluation asset automatically loads the most recently trained model and generates comprehensive metrics including per-class precision, recall, and F1-scores, alongside detailed confusion matrices that reveal systematic error patterns. The asset includes robust error handling for model loading failures while generating rich metadata that enables performance tracking across different training runs and model versions.

## Flexible deployment configuration

Production deployment requires balancing model quality, deployment speed, and operational safety. Our deployment system uses configurable strategies that adapt to different organizational needs and risk tolerances:

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/model_assets.py"
  language="python"
  startAfter="start_deployment_config"
  endBefore="end_deployment_config"
  title="src/project_ml/defs/assets/model_assets.py"
/>

This configuration enables multiple deployment scenarios: quality based automatic deployment promotes models meeting accuracy thresholds, manual model selection allows deploying specific versions by name for expert override, and force deployment bypasses quality gates for development environments. The flexible approach supports different strategies across environments—development might use lower thresholds for rapid iteration, while production employs strict quality gates.

## Model storage abstraction

Scalable ML systems require storage solutions that work across development and production environments. Our abstract storage interface enables seamless transitions from local development to cloud based production systems:

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/resources.py"
  language="python"
  startAfter="start_model_storage_interface"
  endBefore="end_model_storage_interface"
  title="src/project_ml/defs/resources.py"
/>

The storage abstraction supports both local filesystem storage for development experimentation and cloud based S3 storage for production durability and scalability. This design allows the same deployment logic to work across different environments while providing the persistence characteristics needed for each scenario—immediate access for development, durability and multi region support for production.

## Inference services and prediction endpoints

Production ML systems serve predictions through different patterns depending on requirements. Our system supports both batch processing for high throughput scenarios and real-time inference for interactive applications:

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/prediction_assets.py"
  language="python"
  startAfter="start_batch_prediction_config"
  endBefore="end_batch_prediction_config"
  title="src/project_ml/defs/assets/prediction_assets.py"
/>

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/prediction_assets.py"
  language="python"
  startAfter="start_realtime_prediction_config"
  endBefore="end_realtime_prediction_config"
  title="src/project_ml/defs/assets/prediction_assets.py"
/>

Batch inference optimizes for throughput through vectorized operations and GPU utilization, ideal for overnight processing or analytical workloads. Real-time inference prioritizes latency for interactive applications, with configurable confidence thresholds and optional probability distribution returns. Both services include comprehensive error handling and monitoring capabilities essential for production deployment.

## Production monitoring and quality assurance

The complete system demonstrates several production ready capabilities: automated quality gates prevent low-performing models from reaching production while providing override mechanisms for expert judgment, comprehensive metadata generation throughout the pipeline enables performance tracking and debugging, and configurable storage backends support seamless transitions from development to production environments.

Model versioning enables rapid rollback when new deployments cause issues, while confidence scoring in inference services allows routing uncertain predictions to human review. The asset based architecture provides clear dependency tracking and lineage visualization, essential for debugging model performance issues and ensuring reproducible results.

This foundation supports extending to more complex scenarios like multi model ensembles, advanced architectures, distributed training, and integration with MLOps platforms while maintaining the same clear structure and comprehensive observability that makes the system reliable and maintainable.

## Summary

This tutorial demonstrated building a complete production ready ML pipeline using Dagster and PyTorch, covering data ingestion through model deployment and inference. The asset based architecture provides clear dependencies, comprehensive metadata, and flexible configuration while supporting both development experimentation and production reliability requirements.
