import {useQuery, gql} from '@apollo/client';
import {Box, NonIdealState} from '@dagster-io/ui';
import React from 'react';

import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {INSTIGATION_STATE_FRAGMENT} from '../instigation/InstigationUtils';
import {UnloadableSensors} from '../instigation/Unloadable';
import {InstigationType} from '../types/globalTypes';
import {Loading} from '../ui/Loading';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {SENSOR_FRAGMENT} from './SensorFragment';
import {SensorInfo} from './SensorInfo';
import {SensorsTable} from './SensorsTable';
import {SensorsRootQuery, SensorsRootQueryVariables} from './types/SensorsRootQuery';

interface Props {
  repoAddress: RepoAddress;
}

export const SensorsRoot = (props: Props) => {
  useTrackPageView();
  useDocumentTitle('Sensors');

  const {repoAddress} = props;
  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<SensorsRootQuery, SensorsRootQueryVariables>(SENSORS_ROOT_QUERY, {
    variables: {
      repositorySelector,
      instigationType: InstigationType.SENSOR,
    },
    fetchPolicy: 'cache-and-network',
    partialRefetch: true,
    notifyOnNetworkStatusChange: true,
  });

  useQueryRefreshAtInterval(queryResult, 50 * 1000);

  return (
    <Loading queryResult={queryResult} allowStaleData={true}>
      {(result) => {
        const {sensorsOrError, unloadableInstigationStatesOrError, instance} = result;
        const content = () => {
          if (sensorsOrError.__typename === 'PythonError') {
            return <PythonErrorInfo error={sensorsOrError} />;
          } else if (unloadableInstigationStatesOrError.__typename === 'PythonError') {
            return <PythonErrorInfo error={unloadableInstigationStatesOrError} />;
          } else if (sensorsOrError.__typename === 'RepositoryNotFoundError') {
            return (
              <Box padding={{vertical: 64}}>
                <NonIdealState
                  icon="error"
                  title="Repository not found"
                  description="Could not load this repository."
                />
              </Box>
            );
          } else if (!sensorsOrError.results.length) {
            return (
              <Box padding={{vertical: 64}}>
                <NonIdealState
                  icon="sensors"
                  title="No Sensors Found"
                  description={
                    <p>
                      This repository does not have any sensors defined. Visit the{' '}
                      <a
                        href="https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        sensors documentation
                      </a>{' '}
                      for more information about creating sensors in Dagster.
                    </p>
                  }
                />
              </Box>
            );
          } else {
            return (
              <>
                {sensorsOrError.results.length > 0 && (
                  <Box padding={{horizontal: 24, vertical: 16}}>
                    <SensorInfo daemonHealth={instance.daemonHealth} />
                  </Box>
                )}
                <SensorsTable repoAddress={repoAddress} sensors={sensorsOrError.results} />
                <UnloadableSensors sensorStates={unloadableInstigationStatesOrError.results} />
              </>
            );
          }
        };

        return <div>{content()}</div>;
      }}
    </Loading>
  );
};

const SENSORS_ROOT_QUERY = gql`
  query SensorsRootQuery(
    $repositorySelector: RepositorySelector!
    $instigationType: InstigationType!
  ) {
    sensorsOrError(repositorySelector: $repositorySelector) {
      __typename
      ...PythonErrorFragment
      ... on Sensors {
        results {
          id
          ...SensorFragment
        }
      }
    }
    unloadableInstigationStatesOrError(instigationType: $instigationType) {
      ... on InstigationStates {
        results {
          id
          ...InstigationStateFragment
        }
      }
      ...PythonErrorFragment
    }
    instance {
      ...InstanceHealthFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
  ${INSTIGATION_STATE_FRAGMENT}
  ${SENSOR_FRAGMENT}
  ${INSTANCE_HEALTH_FRAGMENT}
`;
