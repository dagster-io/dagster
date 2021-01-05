import {useQuery, gql} from '@apollo/client';
import {NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import React from 'react';

import {JOB_STATE_FRAGMENT} from 'src/JobUtils';
import {Loading} from 'src/Loading';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {INSTANCE_HEALTH_FRAGMENT} from 'src/instance/InstanceHealthFragment';
import {UnloadableSensors} from 'src/jobs/UnloadableJobs';
import {SENSOR_FRAGMENT} from 'src/sensors/SensorFragment';
import {SensorInfo} from 'src/sensors/SensorInfo';
import {SensorsTable} from 'src/sensors/SensorsTable';
import {SensorsRootQuery} from 'src/sensors/types/SensorsRootQuery';
import {JobType} from 'src/types/globalTypes';
import {Group} from 'src/ui/Group';
import {Page} from 'src/ui/Page';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';

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
      jobType: JobType.SENSOR,
    },
    fetchPolicy: 'cache-and-network',
    pollInterval: 50 * 1000,
    partialRefetch: true,
  });

  return (
    <Page>
      <Loading queryResult={queryResult} allowStaleData={true}>
        {(result) => {
          const {sensorsOrError, unloadableJobStatesOrError, instance} = result;
          const content = () => {
            if (sensorsOrError.__typename === 'PythonError') {
              return <PythonErrorInfo error={sensorsOrError} />;
            } else if (unloadableJobStatesOrError.__typename === 'PythonError') {
              return <PythonErrorInfo error={unloadableJobStatesOrError} />;
            } else if (sensorsOrError.__typename === 'RepositoryNotFoundError') {
              return (
                <NonIdealState
                  icon={IconNames.ERROR}
                  title="Repository not found"
                  description="Could not load this repository."
                />
              );
            } else {
              return (
                <Group direction="column" spacing={20}>
                  {sensorsOrError.results.length > 0 && (
                    <SensorInfo daemonHealth={instance.daemonHealth} />
                  )}
                  <SensorsTable repoAddress={repoAddress} sensors={sensorsOrError.results} />
                  <UnloadableSensors sensorStates={unloadableJobStatesOrError.results} />
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
  query SensorsRootQuery($repositorySelector: RepositorySelector!, $jobType: JobType!) {
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
    unloadableJobStatesOrError(jobType: $jobType) {
      ... on JobStates {
        results {
          id
          ...JobStateFragment
        }
      }
      ...PythonErrorFragment
    }
    instance {
      ...InstanceHealthFragment
    }
  }
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${JOB_STATE_FRAGMENT}
  ${SENSOR_FRAGMENT}
  ${INSTANCE_HEALTH_FRAGMENT}
`;
