---
title: Model deployment and inference
description: Deploy trained models to production and serve real-time predictions
last_update:
  author: Dennis Hume
sidebar_position: 50
---

# Model deployment and inference

The transition from trained models to production inference services represents a critical phase where machine learning research becomes business value. This section explores how to build robust deployment pipelines with quality gates, flexible strategies, and scalable inference endpoints.

## Flexible deployment strategies

Production model deployment requires balancing model quality, deployment speed, rollback capabilities, and operational safety. Our deployment system addresses these concerns through configurable strategies that adapt to different organizational needs and risk tolerances.

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/model_assets.py"
  language="python"
  startAfter="start_deployment_config"
  endBefore="end_deployment_config"
  title="Configurable deployment strategies"
/>

This configuration-driven approach enables multiple deployment scenarios within our ML pipeline:

**Quality-based automatic deployment**: Models that meet predefined accuracy thresholds are automatically promoted to production, ensuring consistent quality standards while reducing manual oversight. This works well for established ML systems with well-understood performance criteria.

**Manual model selection**: Production scenarios often require human judgment beyond automated metrics. The system supports deploying specific model versions by name, enabling expert override for debugging production issues, A/B testing different approaches, or implementing gradual rollouts.

**Force deployment capabilities**: Development and testing environments need flexibility to deploy experimental models that might not meet production quality standards. Force deployment bypasses all quality gates, enabling rapid experimentation while maintaining safety through environment isolation.

**Environment-specific configuration**: Different environments use different strategies—development might employ lower thresholds and force deployment for rapid iteration, while production uses strict quality gates and automatic deployment based on rigorous evaluation criteria.

## Model storage and inference architecture

Scalable ML systems require storage solutions that handle both development experimentation and production reliability, along with inference services that serve predictions through different patterns depending on requirements.

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/resources.py"
  language="python"
  startAfter="start_model_storage_interface"
  endBefore="end_model_storage_interface"
  title="Abstract model storage interface"
/>

The storage architecture provides seamless transitions between local development and cloud production systems through abstract interfaces that support both local filesystem storage (for development experimentation and debugging) and cloud-based S3 storage (for production durability, scalability, and multi-region accessibility).

Our inference system supports both batch and real-time prediction scenarios:

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/prediction_assets.py"
  language="python"
  startAfter="start_batch_prediction_config"
  endBefore="end_batch_prediction_config"
  title="Batch inference for high-throughput processing"
/>

<CodeExample
  path="docs_projects/project_ml/src/project_ml/defs/assets/prediction_assets.py"
  language="python"
  startAfter="start_realtime_prediction_config"
  endBefore="end_realtime_prediction_config"
  title="Real-time inference for low-latency responses"
/>

**Batch processing** optimizes for throughput over latency, processing large collections of inputs efficiently through vectorized operations and GPU utilization. This pattern works well for overnight processing, ETL pipelines, or analytical workloads where immediate results aren't required.

**Real-time services** prioritize latency over throughput, optimizing for fast responses to individual predictions with confidence scoring, robust error handling, and adaptive user experiences based on prediction certainty.

**Confidence monitoring**: Both services include prediction confidence scoring that enables routing uncertain predictions to human review, adjusting user interfaces based on prediction certainty, and tracking confidence distributions to identify potential model degradation or data drift.

## Production deployment and monitoring

Production ML systems require comprehensive operational practices to ensure reliable model deployment and inference at scale:

**Model versioning and rollback**: The versioned model storage system enables rapid rollback to known-good model versions when new deployments cause issues, essential for maintaining service reliability during model updates.

**Comprehensive monitoring**: Production inference services track prediction latency, error rates, confidence distributions, and resource utilization, enabling proactive identification of issues before they impact users through alerts and automated responses.

**Scalability and integration**: Production systems handle varying load patterns through horizontal scaling strategies, model caching, and load balancing. ML inference services integrate into larger applications through RESTful API endpoints, message queue processing for asynchronous prediction, streaming pipelines for real-time data processing, or embedded inference for minimal latency.

**Security and compliance**: Production deployments accommodate encryption, access controls, and audit logging requirements while maintaining performance and reliability standards necessary for business-critical applications.

**Operational excellence**: Ongoing operational attention includes performance optimization through latency and throughput analysis, model refresh strategies for maintaining relevance, cost management through efficient resource utilization, and disaster recovery through backup models and failover strategies.

## Tutorial achievements and next steps

This tutorial demonstrated building a complete end-to-end machine learning pipeline that transforms raw MNIST data into production-ready digit classification services:

✅ **Robust data ingestion** with automatic downloading, preprocessing, and stratified validation splits using Dagster assets with comprehensive metadata tracking

✅ **Configurable model training** featuring CNN architecture with modern techniques like batch normalization, dropout, early stopping, and comprehensive hyperparameter control through Dagster's configuration system

✅ **Comprehensive model evaluation** with multi-metric assessment, confusion matrix analysis, and automated quality gates ensuring only high-performing models reach production

✅ **Flexible deployment strategies** supporting automatic quality-based deployment, manual model selection, and force deployment with configurable storage backends that work across environments

✅ **Production-ready inference** through both batch processing for high-throughput scenarios and real-time prediction endpoints with confidence scoring and monitoring capabilities

**Architecture benefits**: The system demonstrates configuration-driven flexibility enabling different strategies across environments, comprehensive observability through rich metadata and logging, scalable storage abstraction for seamless local-to-cloud transitions, and quality assurance integration preventing low-performing models from reaching production.

**Extension opportunities**: This foundation supports extending to multi-model ensembles, advanced architectures like ResNets or Vision Transformers, distributed training for larger datasets, MLOps integration with platforms like MLflow, and real-world deployment through containerization and Kubernetes integration.

The patterns and practices demonstrated here provide the foundation for building reliable, scalable machine learning systems that deliver consistent business value through automated, observable, and maintainable ML pipelines.
