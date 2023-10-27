import numpy
import onnxruntime as rt
from dagster import AssetExecutionContext, AssetIn, AssetOut, asset, multi_asset
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


@asset(
    name="my_joblib_serialized_model",
    compute_kind="wandb",
    metadata={
        "wandb_artifact_configuration": {
            "type": "model",
            "serialization_module": {
                "name": "joblib",
                "parameters": {"compress": 3, "protocol": 4},
            },
        }
    },
)
def create_model_serialized_with_joblib():
    # This is not a real ML model but this would not be possible with the pickle module
    return lambda x, y: x + y


@asset(
    name="inference_result_from_joblib_serialized_model",
    compute_kind="wandb",
    ins={"my_joblib_serialized_model": AssetIn()},
    metadata={
        "wandb_artifact_configuration": {
            "type": "results",
        }
    },
)
def use_model_serialized_with_joblib(context: AssetExecutionContext, my_joblib_serialized_model):
    inference_result = my_joblib_serialized_model(1, 2)
    context.log.info(inference_result)  # Prints: 3
    return inference_result


@multi_asset(
    compute_kind="wandb",
    outs={
        "my_onnx_model": AssetOut(
            metadata={
                "wandb_artifact_configuration": {
                    "type": "model",
                }
            },
        ),
        "my_test_set": AssetOut(
            metadata={
                "wandb_artifact_configuration": {
                    "type": "test_set",
                }
            },
        ),
    },
    group_name="onnx_example",
)
def create_onnx_model():
    # Inspired from https://onnx.ai/sklearn-onnx/

    # Train a model.
    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, X_test, y_train, y_test = train_test_split(X, y)
    clr = RandomForestClassifier()
    clr.fit(X_train, y_train)

    # Convert into ONNX format
    initial_type = [("float_input", FloatTensorType([None, 4]))]
    onx = convert_sklearn(clr, initial_types=initial_type)

    # Write artifacts (model + test_set)
    return onx.SerializeToString(), {"X_test": X_test, "y_test": y_test}


@asset(
    name="experiment_results",
    compute_kind="wandb",
    ins={
        "my_onnx_model": AssetIn(),
        "my_test_set": AssetIn(),
    },
    group_name="onnx_example",
)
def use_onnx_model(context, my_onnx_model, my_test_set):
    # Inspired from https://onnx.ai/sklearn-onnx/

    # Compute the prediction with ONNX Runtime
    sess = rt.InferenceSession(my_onnx_model)
    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name
    pred_onx = sess.run([label_name], {input_name: my_test_set["X_test"].astype(numpy.float32)})[0]
    context.log.info(pred_onx)
    return pred_onx
