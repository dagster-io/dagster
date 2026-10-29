import {Tag, Tooltip} from '@dagster-io/ui-components';
import {useMemo} from 'react';

import {gql, useQuery} from '../apollo-client';
import {RetriedStepsQuery, RetriedStepsQueryVariables} from './types/RunRetriedTag.types';

// Steps with more than one attempt failed and were retried by their retry
// policy. The run can still end in success, so lists call it out per run.
const RETRY_POLL_MS = 15000;

/** Retried step keys for each of the given runs, keyed by run id. */
export const useRetriedSteps = (runIds: string[]) => {
  const {data} = useQuery<RetriedStepsQuery, RetriedStepsQueryVariables>(RETRIED_STEPS_QUERY, {
    variables: {runIds},
    skip: !runIds.length,
    pollInterval: RETRY_POLL_MS,
  });
  return useMemo(() => {
    const map = new Map<string, string[]>();
    if (data?.runsOrError.__typename === 'Runs') {
      data.runsOrError.results.forEach((run) => {
        const retried = run.stepStats.filter((s) => s.attempts.length > 1).map((s) => s.stepKey);
        if (retried.length) {
          map.set(run.runId, retried);
        }
      });
    }
    return map;
  }, [data]);
};

/** Yellow "Retried" tag naming the retried steps on hover. Nothing if none. */
export const RetriedTag = ({steps, short}: {steps?: string[]; short?: boolean}) => {
  if (!steps?.length) {
    return null;
  }
  return (
    <Tooltip
      content={
        <div>
          {steps.map((s) => (
            <div key={s}>{s}</div>
          ))}
        </div>
      }
    >
      <Tag intent="warning" icon="replay">
        {short ? 'Retried' : `${steps.length} ${steps.length === 1 ? 'step' : 'steps'} retried`}
      </Tag>
    </Tooltip>
  );
};

export const RunRetriedTag = ({runId}: {runId: string}) => {
  const retried = useRetriedSteps(useMemo(() => [runId], [runId]));
  return <RetriedTag steps={retried.get(runId)} />;
};

export const RETRIED_STEPS_QUERY = gql`
  query RetriedStepsQuery($runIds: [String!]!) {
    runsOrError(filter: {runIds: $runIds}, limit: 500) {
      ... on Runs {
        results {
          id
          runId
          stepStats {
            stepKey
            attempts {
              startTime
            }
          }
        }
      }
    }
  }
`;
