import {gql, useQuery} from '@apollo/client';
import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';

import {DagsterTag} from '../runs/RunTag';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {Subheading} from '../ui/Text';
import {PreviousRunsSection, PREVIOUS_RUNS_FRAGMENT} from '../workspace/PreviousRunsSection';
import {RepoAddress} from '../workspace/types';

import {PreviousRunsForSensorQuery} from './types/PreviousRunsForSensorQuery';
import {SensorFragment} from './types/SensorFragment';

const RUNS_LIMIT = 20;

export const SensorPreviousRuns: React.FC<{
  sensor: SensorFragment;
  repoAddress: RepoAddress;
  highlightedIds: string[];
}> = ({sensor, highlightedIds}) => {
  const {data, loading} = useQuery<PreviousRunsForSensorQuery>(PREVIOUS_RUNS_FOR_SENSOR_QUERY, {
    fetchPolicy: 'cache-and-network',
    variables: {
      limit: RUNS_LIMIT,
      filter: {
        pipelineName: sensor.targets?.length === 1 ? sensor.targets[0].pipelineName : undefined,
        tags: [{key: DagsterTag.SensorName, value: sensor.name}],
      },
    },
  });

  return (
    <PreviousRunsSection
      loading={loading}
      data={data?.pipelineRunsOrError}
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
        padding={{bottom: 12}}
        border={{side: 'bottom', width: 1, color: ColorsWIP.Gray100}}
        flex={{direction: 'row'}}
      >
        <Subheading>Latest runs</Subheading>
      </Box>
      <div style={{color: ColorsWIP.Gray400}}>
        <Box margin={{vertical: 64}}>
          <NonIdealState description="Sensor does not target a pipeline." />
        </Box>
      </div>
    </Group>
  );
};

const PREVIOUS_RUNS_FOR_SENSOR_QUERY = gql`
  query PreviousRunsForSensorQuery($filter: PipelineRunsFilter, $limit: Int) {
    pipelineRunsOrError(filter: $filter, limit: $limit) {
      __typename
      ...PreviousRunsFragment
    }
  }
  ${PREVIOUS_RUNS_FRAGMENT}
`;
