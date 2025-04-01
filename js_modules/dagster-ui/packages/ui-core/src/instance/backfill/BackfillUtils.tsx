import {gql} from '../../apollo-client';
import {PYTHON_ERROR_FRAGMENT} from '../../app/PythonErrorFragment';

export const LAUNCH_PARTITION_BACKFILL_MUTATION = gql`
  mutation LaunchPartitionBackfill($backfillParams: LaunchBackfillParams!) {
    launchPartitionBackfill(backfillParams: $backfillParams) {
      ... on LaunchBackfillSuccess {
        backfillId
      }
      ... on PartitionSetNotFoundError {
        message
      }
      ... on PartitionKeysNotFoundError {
        message
      }
      ... on InvalidStepError {
        invalidStepKey
      }
      ... on InvalidOutputError {
        stepKey
        invalidOutputName
      }
      ... on UnauthorizedError {
        message
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on RunConflict {
        message
      }
      ... on ConflictingExecutionParamsError {
        message
      }
      ... on PresetNotFoundError {
        message
      }
      ... on RunConfigValidationInvalid {
        pipelineName
        errors {
          message
          path
          reason
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
