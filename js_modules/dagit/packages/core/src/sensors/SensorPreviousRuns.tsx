import {useQuery} from '@apollo/client';
import {Box, Colors, Group, NonIdealState, Subheading} from '@dagster-io/ui';
import * as React from 'react';

import {graphql} from '../graphql';
import {SensorFragmentFragment} from '../graphql/graphql';
import {RunTable} from '../runs/RunTable';
import {DagsterTag} from '../runs/RunTag';
import {RepoAddress} from '../workspace/types';

const RUNS_LIMIT = 20;

export const SensorPreviousRuns: React.FC<{
  sensor: SensorFragmentFragment;
  repoAddress: RepoAddress;
  tabs?: React.ReactElement;
  highlightedIds?: string[];
}> = ({sensor, highlightedIds, tabs}) => {
  const {data} = useQuery(PREVIOUS_RUNS_FOR_SENSOR_QUERY, {
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
  return <RunTable actionBarComponents={tabs} runs={runs} highlightedIds={highlightedIds} />;
};

export const NoTargetSensorPreviousRuns: React.FC<{
  sensor: SensorFragmentFragment;
  repoAddress: RepoAddress;
  highlightedIds: string[];
}> = () => {
  return (
    <Group direction="column" spacing={4}>
      <Box
        padding={{vertical: 16, horizontal: 24}}
        border={{side: 'bottom', width: 1, color: Colors.Gray100}}
        flex={{direction: 'row'}}
      >
        <Subheading>Latest runs</Subheading>
      </Box>
      <div style={{color: Colors.Gray400}}>
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

const PREVIOUS_RUNS_FOR_SENSOR_QUERY = graphql(`
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
`);
