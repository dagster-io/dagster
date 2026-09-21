ANOMALY_DETECTION_INFERENCE_MUTATION = """
mutation AnomalyDetectionInferenceMutation($modelVersion: String!, $params: GenericScalar!) {
  anomalyDetectionInference(modelVersion: $modelVersion, params: $params) {
    __typename
    ... on AnomalyDetectionSuccess {
      response
    }
    ... on AnomalyDetectionFailure {
      message
    }
    ... on PythonError {
      message
      stack
    }
  }
}
"""
