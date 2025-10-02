# ML Repository

The ML Platform team's repository (`repo-ml/`) demonstrates advanced machine learning workflows that build upon the Analytics team's foundational data. This repository showcases how to implement feature engineering, model training, and prediction pipelines while maintaining dependencies on assets from another code location.

## Repository Structure

The ML repository is organized around machine learning workflows and model lifecycle management:

```
repo-ml/
├── dagster_cloud.yaml                # Dagster+ deployment config
├── pyproject.toml                   # Python dependencies (includes ML libraries)
├── src/ml_platform/
│   ├── definitions.py               # Main definitions entry point
│   └── defs/
│       ├── io_managers.py           # Resource configurations
│       └── models/
│           ├── features.py          # Feature engineering assets
│           └── training.py          # Model training and prediction assets
```

The repository uses a `models/` subdirectory to organize ML-specific assets, clearly separating feature engineering from model training and prediction workflows.

## Cross-Repository Feature Engineering

The ML team creates features by consuming and transforming assets from the Analytics repository:

<CodeExample
  path="docs_projects/project_multi_repo/repo-ml/src/ml_platform/defs/models/features.py"
  language="python"
  startAfter="start_load_external_asset"
  endBefore="end_load_external_asset"
  title="features.py - External Asset Loading"
/>

The `load_external_asset` utility function provides a simple way to access assets materialized by other code locations. This pattern gives the ML team explicit control over external dependencies while maintaining loose coupling between repositories.

## Customer Feature Engineering

The ML repository transforms analytics data into machine learning features:

<CodeExample
  path="docs_projects/project_multi_repo/repo-ml/src/ml_platform/defs/models/features.py"
  language="python"
  startAfter="start_customer_features"
  endBefore="end_customer_features"
  title="features.py - Customer Features Asset"
/>

The `customer_features` asset demonstrates sophisticated feature engineering patterns:

- **Temporal Features**: Calculates days since last order and customer lifecycle metrics
- **Behavioral Features**: Derives order frequency and purchase patterns
- **RFM Analysis**: Implements Recency, Frequency, and Monetary scoring for customer segmentation
- **Categorical Encoding**: Transforms customer tier information into model-ready features

The asset explicitly declares its dependency on `customer_order_summary` from the Analytics repository using `deps=[AssetKey("customer_order_summary")]`, ensuring proper lineage tracking across code locations.

## Model Training and Validation

The ML repository implements complete model training workflows with proper validation and metrics tracking:

<CodeExample
  path="docs_projects/project_multi_repo/repo-ml/src/ml_platform/defs/models/training.py"
  language="python"
  startAfter="start_customer_churn_model"
  endBefore="end_customer_churn_model"
  title="training.py - Customer Churn Model"
/>

The `customer_churn_model` asset showcases production-ready ML practices:

- **Synthetic Label Generation**: Creates realistic churn labels based on customer behavior patterns
- **Feature Selection**: Uses specific feature columns optimized for the prediction task
- **Model Training**: Implements Random Forest classification with proper train/test splits
- **Comprehensive Evaluation**: Tracks accuracy, precision, recall, and F1 scores
- **Feature Importance**: Captures and returns feature importance for model interpretability

The asset returns a dictionary containing both the trained model and comprehensive metadata, enabling downstream assets to access both predictions and model performance insights.

## Demand Forecasting Pipeline

The ML repository also includes regression models for business forecasting:

<CodeExample
  path="docs_projects/project_multi_repo/repo-ml/src/ml_platform/defs/models/training.py"
  language="python"
  startAfter="start_demand_forecast_model"
  endBefore="end_demand_forecast_model"
  title="training.py - Demand Forecast Model"
/>

The `demand_forecast_model` demonstrates regression modeling patterns:

- **Multi-Feature Input**: Uses product performance metrics, profitability data, and categorical features
- **Target Variable Engineering**: Creates synthetic demand based on realistic business drivers
- **Regression Metrics**: Tracks MSE, RMSE, and R² scores for model performance
- **Cross-Category Features**: Handles categorical variables through one-hot encoding

## Production Prediction Assets

The ML repository includes assets that generate business-ready predictions:

<CodeExample
  path="docs_projects/project_multi_repo/repo-ml/src/ml_platform/defs/models/training.py"
  language="python"
  startAfter="start_customer_risk_scores"
  endBefore="end_customer_risk_scores"
  title="training.py - Customer Risk Scoring"
/>

The `customer_risk_scores` asset demonstrates how to deploy trained models for business use:

- **Probabilistic Predictions**: Generates churn probabilities for all customers
- **Risk Tiering**: Segments customers into Low, Medium, and High risk categories
- **Actionable Recommendations**: Provides specific business actions for each risk tier

This pattern ensures that ML models produce business-ready outputs that non-technical stakeholders can immediately understand and act upon.

## Asset Organization and ML Groups

The ML repository uses specialized asset groups for machine learning workflows:

- **`ml_features` group**: Feature engineering and data preparation assets
- **`ml_models` group**: Model training and validation assets
- **`ml_predictions` group**: Production prediction and scoring assets

This organization pattern helps ML practitioners understand the model development lifecycle and ensures clear separation between data preparation, model development, and production deployment phases.

## Next steps

Now that we understand how both repositories work individually, we can explore the technical details of how assets depend on each other across repository boundaries and how data flows between teams.

- Continue this tutorial with [Cross-Repository Dependencies](/examples/full-pipelines/multi-repo/cross-repository-dependencies)
