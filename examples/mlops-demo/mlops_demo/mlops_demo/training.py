from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, recall_score, precision_score
import polars as pl
import dagster as dg

asset_groups = {
    "ingestion": "data_ingestion",
    "training": "model_training",
    "inference": "model_inference"
}

train_fraction = 0.7
test_fraction = 1 - train_fraction

cleaned_readings_fn = "cleaned_readings.jsonl"
cleaned_daily_statuses_fn = "cleaned_daily_statuses.jsonl"

@dg.asset(
    description="Overlap between readings and statuses",
    group_name=asset_groups["training"],
    kinds={"polars"},
)
def joined_cleaned_readings_and_statuses(context: dg.AssetExecutionContext,  historical_readings: int, historical_daily_statuses: int) -> pl.DataFrame:

    with open(cleaned_readings_fn, "r") as f:
        df_readings = pl.read_ndjson(f)
    with open(cleaned_daily_statuses_fn, "r") as f:
        df_statuses = pl.read_ndjson(f)

    df = df_readings.join(df_statuses, on="UDI", how="inner")

    context.add_output_metadata({
        "num_matches": len(df)
    })

    return df


@dg.asset(
    description="The training part of the dataset",
    group_name=asset_groups["training"],
)
def training_data(context: dg.AssetExecutionContext, joined_cleaned_readings_and_statuses: pl.DataFrame) -> pl.DataFrame:

    upper_index = int(len(joined_cleaned_readings_and_statuses)*train_fraction)
    df_train = joined_cleaned_readings_and_statuses[0:upper_index]

    num_train_rows = df_train.height
    num_failures = df_train.filter(pl.col("Target") == 1).height
    num_non_failures = df_train.filter(pl.col("Target") == 0).height
    context.add_output_metadata({
        "num_train_rows": num_train_rows,
        "num_failures": num_failures,
        "num_non_failures": num_non_failures
    })

    return df_train
    
    
@dg.asset(
    description="The test part of the dataset",
    group_name=asset_groups["training"],
)
def test_data(context: dg.AssetExecutionContext, joined_cleaned_readings_and_statuses: pl.DataFrame) -> pl.DataFrame:
    lower_index = int(len(joined_cleaned_readings_and_statuses)*train_fraction)
    df_test = joined_cleaned_readings_and_statuses[lower_index:]

    num_test_rows = df_test.height
    num_failures = df_test.filter(pl.col("Target") == 1).height
    num_non_failures = df_test.filter(pl.col("Target") == 0).height
    context.add_output_metadata({
        "num_train_rows": num_test_rows,
        "num_failures": num_failures,
        "num_non_failures": num_non_failures
    })

    return df_test


@dg.asset(
    description="The last trained model (not the production model)",
    group_name=asset_groups["training"]
)
def trained_model(context: dg.AssetExecutionContext, training_data: pl.DataFrame, test_data: pl.DataFrame) -> RandomForestClassifier:

    feature_cols = ["Air temperature [K]", "Process temperature [K]", "Rotational speed [rpm]", "Torque [Nm]"]
    label_col = "Target"

    X_train= training_data[feature_cols]
    y_train = training_data[label_col]
    X_test = test_data[feature_cols]
    y_test = test_data[label_col]
    
    param_grid = {
        'n_estimators': [10, 30],
        'max_depth': [None, 15, 30],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2],
        'max_features': ['sqrt', 'log2']
    }

    clf = RandomForestClassifier(random_state=41, verbose=1)

    grid_search = GridSearchCV(
        estimator=clf,
        param_grid=param_grid,
        cv=3,                # 5-fold cross-validation
        scoring='precision',        # or 'accuracy', 'precision', etc.
        verbose=2
    )

    grid_search.fit(X_train, y_train)

    best_model = grid_search.best_estimator_

    y_pred =best_model.predict(X_test)
    scores = {
        "accuracy": accuracy_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
    }

    context.add_asset_metadata({
        "Classes": dg.MetadataValue.json(best_model.classes_.tolist()),
        "Accuracy": scores["accuracy"],
        "Recall": scores["recall"],
        "Precision": scores["precision"],
    })


    return best_model

train_ml_model_job = dg.define_asset_job(
    "train_ml_model",
    selection=[joined_cleaned_readings_and_statuses, training_data, test_data, trained_model]
)

train_ml_model_schedule = dg.ScheduleDefinition(
    job=train_ml_model_job,
    cron_schedule="*/10 * * * *"
)
