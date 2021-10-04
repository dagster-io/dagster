import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {INSTIGATION_STATE_FRAGMENT} from '../instigation/InstigationUtils';
import {UnloadableSensors} from '../instigation/Unloadable';
import {SENSOR_FRAGMENT} from '../sensors/SensorFragment';
import {SensorInfo} from '../sensors/SensorInfo';
import {SensorsTable} from '../sensors/SensorsTable';
import {InstigationType} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {Loading} from '../ui/Loading';
import {NonIdealState} from '../ui/NonIdealState';
import {Subheading} from '../ui/Text';
import {REPOSITORY_INFO_FRAGMENT} from '../workspace/RepositoryInformation';
import {REPOSITORY_LOCATIONS_FRAGMENT} from '../workspace/WorkspaceContext';
import {buildRepoPath, buildRepoAddress} from '../workspace/buildRepoAddress';

import {INSTANCE_HEALTH_FRAGMENT} from './InstanceHealthFragment';
import {InstanceTabs} from './InstanceTabs';
import {InstanceSensorsQuery} from './types/InstanceSensorsQuery';

const POLL_INTERVAL = 15000;

export const InstanceSensors = React.memo(() => {
  const queryData = useQuery<InstanceSensorsQuery>(INSTANCE_SENSORS_QUERY, {
    fetchPolicy: 'cache-and-network',
    pollInterval: POLL_INTERVAL,
    notifyOnNetworkStatusChange: true,
  });

  return (
    <Group direction="column" spacing={20}>
      <InstanceTabs tab="sensors" queryData={queryData} />
      <Loading queryResult={queryData} allowStaleData={true}>
        {(data) => <AllSensors data={data} />}
      </Loading>
    </Group>
  );
});

const AllSensors: React.FC<{data: InstanceSensorsQuery}> = ({data}) => {
  const {instance, repositoriesOrError, unloadableInstigationStatesOrError} = data;

  if (repositoriesOrError.__typename === 'PythonError') {
    return <PythonErrorInfo error={repositoriesOrError} />;
  }
  if (unloadableInstigationStatesOrError.__typename === 'PythonError') {
    return <PythonErrorInfo error={unloadableInstigationStatesOrError} />;
  }

  const unloadable = unloadableInstigationStatesOrError.results;
  const withSensors = repositoriesOrError.nodes.filter((repository) => repository.sensors.length);

  const sensorDefinitionsSection = withSensors.length ? (
    <Group direction="column" spacing={32}>
      <Box padding={{horizontal: 24}}>
        <SensorInfo daemonHealth={instance.daemonHealth} />
      </Box>
      {withSensors.map((repository) =>
        repository.sensors.length ? (
          <Group direction="column" spacing={12} key={repository.name}>
            <Box padding={{horizontal: 24}}>
              <Subheading>{`${buildRepoPath(
                repository.name,
                repository.location.name,
              )}`}</Subheading>
            </Box>
            <SensorsTable
              repoAddress={buildRepoAddress(repository.name, repository.location.name)}
              sensors={repository.sensors}
            />
          </Group>
        ) : null,
      )}
    </Group>
  ) : null;

  const unloadableSensors = unloadable.filter(
    (state) => state.instigationType === InstigationType.SENSOR,
  );
  const unloadableSensorsSection = unloadableSensors.length ? (
    <UnloadableSensors sensorStates={unloadableSensors} />
  ) : null;

  if (!sensorDefinitionsSection && !unloadableSensorsSection) {
    return (
      <Box margin={{top: 32}}>
        <NonIdealState
          icon="sensors"
          title="No sensors found"
          description={
            <p>
              This instance does not have any sensors defined. Visit the{' '}
              <a
                href="https://docs.dagster.io/overview/schedules-sensors/sensors"
                target="_blank"
                rel="noreferrer"
              >
                sensor documentation
              </a>{' '}
              for more information about setting up sensors in Dagster.
            </p>
          }
        />
      </Box>
    );
  }

  return (
    <Group direction="column" spacing={32}>
      {sensorDefinitionsSection}
      {unloadableSensorsSection}
    </Group>
  );
};

const INSTANCE_SENSORS_QUERY = gql`
  query InstanceSensorsQuery {
    instance {
      ...InstanceHealthFragment
    }
    workspaceOrError {
      ...RepositoryLocationsFragment
    }
    repositoriesOrError {
      __typename
      ... on RepositoryConnection {
        nodes {
          id
          name
          ...RepositoryInfoFragment
          sensors {
            id
            ...SensorFragment
          }
        }
      }
      ...PythonErrorFragment
    }
    unloadableInstigationStatesOrError {
      ... on InstigationStates {
        results {
          id
          ...InstigationStateFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${INSTANCE_HEALTH_FRAGMENT}
  ${REPOSITORY_LOCATIONS_FRAGMENT}
  ${REPOSITORY_INFO_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
  ${SENSOR_FRAGMENT}
  ${INSTIGATION_STATE_FRAGMENT}
`;
