import {gql, useQuery} from '@apollo/client';
import React from 'react';

import {PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {QueryCountdown} from 'src/app/QueryCountdown';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from 'src/instance/InstanceHealthFragment';
import {JOB_STATE_FRAGMENT} from 'src/jobs/JobUtils';
import {AllSensors} from 'src/sensors/AllSensors';
import {SENSOR_FRAGMENT} from 'src/sensors/SensorFragment';
import {AllSensorsQuery} from 'src/sensors/types/AllSensorsQuery';
import {JobType} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {Loading} from 'src/ui/Loading';
import {Page} from 'src/ui/Page';
import {Heading} from 'src/ui/Text';

const POLL_INTERVAL = 15 * 1000;

export const AllSensorsRoot = () => {
  useDocumentTitle('Sensors');

  const queryResult = useQuery<AllSensorsQuery>(ALL_SENSORS_QUERY, {
    fetchPolicy: 'cache-and-network',
    pollInterval: POLL_INTERVAL,
    partialRefetch: true,
    notifyOnNetworkStatusChange: true,
    variables: {
      jobType: JobType.SENSOR,
    },
  });

  return (
    <Page style={{height: '100vh', width: '100%', overflowY: 'auto'}}>
      <Box flex={{alignItems: 'flex-end', justifyContent: 'space-between'}} margin={{bottom: 20}}>
        <Heading>Sensors</Heading>
        <QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryResult} />
      </Box>
      <Loading allowStaleData queryResult={queryResult}>
        {(data) => <AllSensors {...data} />}
      </Loading>
    </Page>
  );
};

const REPOSITORIES_FRAGMENT = gql`
  fragment AllSensorsRepositoriesFragment on RepositoriesOrError {
    ... on RepositoryConnection {
      nodes {
        id
        name
        location {
          id
          name
        }
        sensors {
          id
          ...SensorFragment
        }
      }
    }
    ...PythonErrorFragment
  }

  ${SENSOR_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

const UNLOADABLES_FRAGMENT = gql`
  fragment AllSensorsUnloadablesFragment on JobStatesOrError {
    ... on JobStates {
      results {
        id
        ...JobStateFragment
      }
    }
    ...PythonErrorFragment
  }

  ${JOB_STATE_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
`;

export const ALL_SENSORS_QUERY = gql`
  query AllSensorsQuery($jobType: JobType) {
    repositoriesOrError {
      ...AllSensorsRepositoriesFragment
    }
    instance {
      ...InstanceHealthFragment
    }
    unloadableJobStatesOrError(jobType: $jobType) {
      ...AllSensorsUnloadablesFragment
    }
  }

  ${REPOSITORIES_FRAGMENT}
  ${INSTANCE_HEALTH_FRAGMENT}
  ${UNLOADABLES_FRAGMENT}
`;
