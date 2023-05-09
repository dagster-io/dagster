import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {RunTable, RUN_TABLE_RUN_FRAGMENT} from '../runs/RunTable';
import {DagsterTag} from '../runs/RunTag';
import {RepoAddress} from '../workspace/types';

import {SensorFragment} from './types/SensorFragment.types';
import {
  PreviousRunsForSensorQuery,
  PreviousRunsForSensorQueryVariables,
} from './types/SensorPreviousRuns.types';

const RUNS_LIMIT = 20;

export const SensorPreviousRuns: React.FC<{
  sensor: SensorFragment;
  repoAddress: RepoAddress;
  tabs?: React.ReactElement;
  highlightedIds?: string[];
}> = ({sensor, highlightedIds, tabs}) => {
  const {data} = useQuery<PreviousRunsForSensorQuery, PreviousRunsForSensorQueryVariables>(
    PREVIOUS_RUNS_FOR_SENSOR_QUERY,
    {
      variables: {
        limit: RUNS_LIMIT,
        filter: {
          pipelineName: sensor.targets?.length === 1 ? sensor.targets[0].pipelineName : undefined,
          tags: [{key: DagsterTag.SensorName, value: sensor.name}],
        },
      },
    },
  );

  if (!data || data.pipelineRunsOrError.__typename !== 'Runs') {
    return null;
  }

  const runs = data?.pipelineRunsOrError.results;
  return (
    <RunTable
      actionBarComponents={tabs}
      runs={runs}
      highlightedIds={highlightedIds}
      hideCreatedBy={true}
    />
  );
};

const PREVIOUS_RUNS_FOR_SENSOR_QUERY = gql`
  query PreviousRunsForSensorQuery($filter: RunsFilter, $limit: Int) {
    pipelineRunsOrError(filter: $filter, limit: $limit) {
      ... on Runs {
        results {
          id
          ... on PipelineRun {
            ...RunTableRunFragment
          }
        }
      }
    }
  }

  ${RUN_TABLE_RUN_FRAGMENT}
`;
