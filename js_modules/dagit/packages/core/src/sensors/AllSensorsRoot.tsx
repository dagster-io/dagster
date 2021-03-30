import {gql, useQuery} from '@apollo/client';
import React from 'react';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {QueryCountdown} from '../app/QueryCountdown';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {JOB_STATE_FRAGMENT} from '../jobs/JobUtils';
import {JobType} from '../types/globalTypes';
import {Group} from '../ui/Group';
import {Loading} from '../ui/Loading';
import {Page} from '../ui/Page';
import {PageHeader} from '../ui/PageHeader';
import {Heading} from '../ui/Text';

import {AllSensors} from './AllSensors';
import {SENSOR_FRAGMENT} from './SensorFragment';
import {AllSensorsQuery} from './types/AllSensorsQuery';

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
    <Page>
      <Group direction="column" spacing={16}>
        <PageHeader
          title={<Heading>Sensors</Heading>}
          right={<QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryResult} />}
        />
        <Loading allowStaleData queryResult={queryResult}>
          {(data) => <AllSensors {...data} />}
        </Loading>
      </Group>
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

const ALL_SENSORS_QUERY = gql`
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
