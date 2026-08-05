PUT_CLOUD_METRICS_MUTATION = """
mutation CreateOrUpdateExtenalMetrics(
  $metrics: [MetricInputs]!) {
  createOrUpdateMetrics(metrics: $metrics) {
    __typename
    ... on CreateOrUpdateMetricsSuccess {
      status
      __typename
    }
    ...MetricsFailedFragment
    ...UnauthorizedErrorFragment
    ...PythonErrorFragment
  }
}
fragment PythonErrorFragment on PythonError {
  __typename
  message
  stack
  causes {
    message
    stack
    __typename
  }
}
fragment MetricsFailedFragment on CreateOrUpdateMetricsFailed {
  __typename
  message
}
fragment UnauthorizedErrorFragment on UnauthorizedError {
  __typename
  message
}
"""


PUT_COST_INFORMATION_MUTATION = """
mutation SubmitCostInformation(
  $metricName: String!, $costInfo: [CostInformation!], $start: Float!, $end: Float!) {
  submitCostInformationForMetrics(metricName: $metricName, costInfo: $costInfo, start: $start, end: $end) {
    __typename
    ... on CreateOrUpdateMetricsSuccess {
      status
      __typename
    }
    ...MetricsFailedFragment
    ...UnauthorizedErrorFragment
    ...PythonErrorFragment
  }
}
fragment PythonErrorFragment on PythonError {
  __typename
  message
  stack
  causes {
    message
    stack
    __typename
  }
}
fragment MetricsFailedFragment on CreateOrUpdateMetricsFailed {
  __typename
  message
}
fragment UnauthorizedErrorFragment on UnauthorizedError {
  __typename
  message
}
"""
