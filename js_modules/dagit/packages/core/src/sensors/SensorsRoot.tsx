import {useQuery, gql} from '@apollo/client';
import {NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import React from 'react';

import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from '../instance/InstanceHealthFragment';
import {INSTIGATION_STATE_FRAGMENT} from '../instigation/InstigationUtils';
import {UnloadableSensors} from '../instigation/Unloadable';
import {InstigationType} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {Loading} from '../ui/Loading';
import {Page} from '../ui/Page';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';

import {SENSOR_FRAGMENT} from './SensorFragment';
import {SensorInfo} from './SensorInfo';
import {SensorsTable} from './SensorsTable';
import {SensorsRootQuery} from './types/SensorsRootQuery';

interface Props {
  repoAddress: RepoAddress;
}

export const SensorsRoot = (props: Props) => {
  const {repoAddress} = props;
  useDocumentTitle('Sensors');
  const repositorySelector = repoAddressToSelector(repoAddress);

  const queryResult = useQuery<SensorsRootQuery>(SENSORS_ROOT_QUERY, {
    variables: {
      repositorySelector: repositorySelector,
      instigationType: InstigationType.SENSOR,
    },
    fetchPolicy: 'cache-and-network',
    pollInterval: 50 * 1000,
    partialRefetch: true,
  });

  return (
    <Page>
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
                <NonIdealState
                  icon={IconNames.ERROR}
                  title="Repository not found"
                  description="Could not load this repository."
                />
              );
            } else if (!sensorsOrError.results.length) {
              return (
                <NonIdealState
                  icon={IconNames.AUTOMATIC_UPDATES}
                  title="No Sensors Found"
                  description={
                    <p>
                      This repository does not have any sensors defined. Visit the{' '}
                      <a
                        href="https://docs.dagster.io/overview/schedules-sensors/sensors"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        sensors documentation
                      </a>{' '}
                      for more information about creating sensors in Dagster.
                    </p>
                  }
                />
              );
            } else {
              return (
                <Group direction="column" spacing={20}>
                  {sensorsOrError.results.length > 0 && (
                    <Box padding={{horizontal: 24}}>
                      <SensorInfo daemonHealth={instance.daemonHealth} />
                    </Box>
                  )}
                  <SensorsTable repoAddress={repoAddress} sensors={sensorsOrError.results} />
                  <UnloadableSensors sensorStates={unloadableInstigationStatesOrError.results} />
                </Group>
              );
            }
          };

          return <div>{content()}</div>;
        }}
      </Loading>
    </Page>
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
