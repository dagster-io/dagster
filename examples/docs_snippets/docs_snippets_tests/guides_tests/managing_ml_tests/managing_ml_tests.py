from dagster._core.definitions.load_assets_from_modules import assets_from_modules
from dagster._core.definitions.materialize import materialize
from docs_snippets.guides.dagster.managing_ml.managing_ml_code import (
    my_data, my_ml_model, my_other_data, my_other_ml_model, some_data, some_ml_model, predictions, conditional_machine_learning_model, xgboost_comments_model)

def assets_test():
    result = materialize([my_data, my_ml_model, my_other_data, my_other_ml_model, some_data, some_ml_model, predictions, conditional_machine_learning_model, xgboost_comments_model])
    assert result.success 
