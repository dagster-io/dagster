import {gql, useQuery} from '@apollo/client';
import {Box, ColorsWIP, Group, NonIdealState, Subheading} from '@dagster-io/ui';
import * as React from 'react';

import {DagsterTag} from '../runs/RunTag';
import {RunTable, RUN_TABLE_RUN_FRAGMENT} from '../runs/RunTable';
import {RepoAddress} from '../workspace/types';

import {PreviousRunsForSensorQuery} from './types/PreviousRunsForSensorQuery';
import {SensorFragment} from './types/SensorFragment';

const RUNS_LIMIT = 20;

export const SensorPreviousRuns: React.FC<{
  sensor: SensorFragment;
  repoAddress: RepoAddress;
  tabs?: React.ReactElement;
  highlightedIds?: string[];
}> = ({sensor, highlightedIds, tabs}) => {
  const {data} = useQuery<PreviousRunsForSensorQuery>(PREVIOUS_RUNS_FOR_SENSOR_QUERY, {
    fetchPolicy: 'cache-and-network',
    variables: {
      limit: RUNS_LIMIT,
      filter: {
        pipelineName: sensor.targets?.length === 1 ? sensor.targets[0].pipelineName : undefined,
        tags: [{key: DagsterTag.SensorName, value: sensor.name}],
      },
    },
  });

  if (!data || data.pipelineRunsOrError.__typename !== 'Runs') {
    return null;
  }

  const runs = data?.pipelineRunsOrError.results;
  return (
    <RunTable
      actionBarComponents={tabs}
      onSetFilter={() => {}}
      runs={runs}
      highlightedIds={highlightedIds}
    />
  );
};

export const NoTargetSensorPreviousRuns: React.FC<{
  sensor: SensorFragment;
  repoAddress: RepoAddress;
  highlightedIds: string[];
}> = () => {
  return (
    <Group direction="column" spacing={4}>
      <Box
        padding={{vertical: 16, horizontal: 24}}
        border={{side: 'bottom', width: 1, color: ColorsWIP.Gray100}}
        flex={{direction: 'row'}}
      >
        <Subheading>Latest runs</Subheading>
      </Box>
      <div style={{color: ColorsWIP.Gray400}}>
        <Box margin={{vertical: 64}}>
          <NonIdealState
            icon="sensors"
            title="No runs to display"
            description="This sensor does not target a pipeline or job."
          />
        </Box>
      </div>
    </Group>
  );
};

const PREVIOUS_RUNS_FOR_SENSOR_QUERY = gql`
  query PreviousRunsForSensorQuery($filter: RunsFilter, $limit: Int) {
    pipelineRunsOrError(filter: $filter, limit: $limit) {
      __typename
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
