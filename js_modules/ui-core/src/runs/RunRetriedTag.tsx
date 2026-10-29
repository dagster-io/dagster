import {Tag, Tooltip} from '@dagster-io/ui-components';

import {doneStatuses} from './RunStatuses';
import {gql, useQuery} from '../apollo-client';
import {RunStatus} from '../graphql/types';
import {RunRetriedStepsQuery, RunRetriedStepsQueryVariables} from './types/RunRetriedTag.types';

// A step with more than one attempt failed and was retried by its retry
// policy. The run can still end in success, so the header calls it out.
export const RunRetriedTag = ({runId, status}: {runId: string; status: RunStatus}) => {
  const {data} = useQuery<RunRetriedStepsQuery, RunRetriedStepsQueryVariables>(
    RUN_RETRIED_STEPS_QUERY,
    {variables: {runId}, pollInterval: doneStatuses.has(status) ? 0 : 15000},
  );
  const stats = data?.runOrError.__typename === 'Run' ? data.runOrError.stepStats : [];
  const retried = stats.filter((s) => s.attempts.length > 1);
  if (!retried.length) {
    return null;
  }
  return (
    <Tooltip
      content={
        <div>
          {retried.map((s) => (
            <div key={s.stepKey}>
              {s.stepKey}: retried {s.attempts.length - 1}×
            </div>
          ))}
        </div>
      }
    >
      <Tag intent="warning" icon="replay">
        {retried.length} {retried.length === 1 ? 'step' : 'steps'} retried
      </Tag>
    </Tooltip>
  );
};

export const RUN_RETRIED_STEPS_QUERY = gql`
  query RunRetriedStepsQuery($runId: ID!) {
    runOrError(runId: $runId) {
      ... on Run {
        id
        stepStats {
          stepKey
          attempts {
            startTime
          }
        }
      }
    }
  }
`;
