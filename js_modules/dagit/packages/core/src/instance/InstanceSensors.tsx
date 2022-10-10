import {gql, useQuery} from '@apollo/client';
import {Box, Colors, NonIdealState, PageHeader, Heading, Subheading} from '@dagster-io/ui';
import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {useQueryRefreshAtInterval, FIFTEEN_SECONDS} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {INSTIGATION_STATE_FRAGMENT} from '../instigation/InstigationUtils';
import {UnloadableSensors} from '../instigation/Unloadable';
import {OverviewTabs} from '../overview/OverviewTabs';
import {SENSOR_FRAGMENT} from '../sensors/SensorFragment';
import {SensorInfo} from '../sensors/SensorInfo';
import {SensorsTable} from '../sensors/SensorsTable';
import {Loading} from '../ui/Loading';
import {REPOSITORY_INFO_FRAGMENT} from '../workspace/RepositoryInformation';
import {buildRepoPath, buildRepoAddress} from '../workspace/buildRepoAddress';

import {INSTANCE_HEALTH_FRAGMENT} from './InstanceHealthFragment';
import {InstancePageContext} from './InstancePageContext';
import {InstanceTabs} from './InstanceTabs';
import {InstanceSensorsQuery} from './types/InstanceSensorsQuery';

export const InstanceSensors = React.memo(() => {
  useTrackPageView();
  const {flagNewWorkspace} = useFeatureFlags();

  const {pageTitle} = React.useContext(InstancePageContext);
  const queryData = useQuery<InstanceSensorsQuery>(INSTANCE_SENSORS_QUERY, {
    fetchPolicy: 'cache-and-network',
    notifyOnNetworkStatusChange: true,
  });
  const refreshState = useQueryRefreshAtInterval(queryData, FIFTEEN_SECONDS);

  return (
    <>
      <PageHeader
        title={<Heading>{flagNewWorkspace ? 'Overview' : pageTitle}</Heading>}
        tabs={
          flagNewWorkspace ? (
            <OverviewTabs tab="sensors" />
          ) : (
            <InstanceTabs tab="sensors" refreshState={refreshState} />
          )
        }
      />
      <Loading queryResult={queryData} allowStaleData={true}>
        {(data) => <AllSensors data={data} />}
      </Loading>
    </>
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
    <>
      <SensorInfo daemonHealth={instance.daemonHealth} padding={{horizontal: 24, vertical: 16}} />
      {withSensors.map((repository) =>
        repository.sensors.length ? (
          <React.Fragment key={repository.name}>
            <Box
              padding={{horizontal: 24, vertical: 16}}
              border={{side: 'top', width: 1, color: Colors.KeylineGray}}
            >
              <Subheading>{`${buildRepoPath(
                repository.name,
                repository.location.name,
              )}`}</Subheading>
            </Box>
            <Box padding={{bottom: 16}}>
              <SensorsTable
                repoAddress={buildRepoAddress(repository.name, repository.location.name)}
                sensors={repository.sensors}
              />
            </Box>
          </React.Fragment>
        ) : null,
      )}
    </>
  ) : null;

  const unloadableSensorsSection = unloadable.length ? (
    <UnloadableSensors sensorStates={unloadable} />
  ) : null;

  if (!sensorDefinitionsSection && !unloadableSensorsSection) {
    return (
      <Box padding={{vertical: 64}} border={{side: 'top', width: 1, color: Colors.KeylineGray}}>
        <NonIdealState
          icon="sensors"
          title="No sensors found"
          description={
            <p>
              This instance does not have any sensors defined. Visit the{' '}
              <a
                href="https://docs.dagster.io/concepts/partitions-schedules-sensors/schedules"
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
    <>
      {sensorDefinitionsSection}
      {unloadableSensorsSection}
    </>
  );
};

const INSTANCE_SENSORS_QUERY = gql`
  query InstanceSensorsQuery {
    instance {
      ...InstanceHealthFragment
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
    unloadableInstigationStatesOrError(instigationType: SENSOR) {
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
  ${REPOSITORY_INFO_FRAGMENT}
  ${PYTHON_ERROR_FRAGMENT}
  ${SENSOR_FRAGMENT}
  ${INSTIGATION_STATE_FRAGMENT}
`;
