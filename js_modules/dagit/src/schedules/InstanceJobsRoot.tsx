import {gql, useQuery} from '@apollo/client';
import {Colors, NonIdealState} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import React from 'react';

import {ScrollContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {
  REPOSITORY_SCHEDULES_FRAGMENT,
  SCHEDULE_DEFINITION_FRAGMENT,
  SCHEDULE_STATE_FRAGMENT,
  SchedulerTimezoneNote,
} from 'src/schedules/ScheduleUtils';
import {SCHEDULER_FRAGMENT, SchedulerInfo} from 'src/schedules/SchedulerInfo';
import {SchedulesTable, UnLoadableSchedules} from 'src/schedules/SchedulesRoot';
import {InstanceJobsRootQuery} from 'src/schedules/types/InstanceJobsRootQuery';
import {JOB_STATE_FRAGMENT, SENSOR_FRAGMENT} from 'src/sensors/SensorFragment';
import {SensorsTable, UnloadableSensors} from 'src/sensors/SensorsTable';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Heading, Subheading} from 'src/ui/Text';

export const InstanceJobsRoot = () => {
  useDocumentTitle('Scheduler');
  const queryResult = useQuery<InstanceJobsRootQuery>(INSTANCE_JOBS_ROOT_QUERY, {
    variables: {},
    fetchPolicy: 'cache-and-network',
  });

  return (
    <ScrollContainer>
      <div style={{padding: '16px'}}>
        <Loading queryResult={queryResult} allowStaleData={true}>
          {(result) => {
            const {
              scheduler,
              repositoriesOrError,
              unLoadableScheduleStates,
              unloadableSensorStatesOrError,
            } = result;

            let unLoadableSchedules = null;

            if (repositoriesOrError.__typename === 'PythonError') {
              return <PythonErrorInfo error={repositoriesOrError} />;
            }
            if (unLoadableScheduleStates.__typename === 'PythonError') {
              return <PythonErrorInfo error={unLoadableScheduleStates} />;
            } else if (unLoadableScheduleStates.__typename === 'RepositoryNotFoundError') {
              return (
                <NonIdealState
                  icon={IconNames.ERROR}
                  title="Unexpected RepositoryNotFoundError"
                  description="InstanceJobsRootQuery unexpectedly returned a RepositoryNotFoundError."
                />
              );
            } else {
              unLoadableSchedules = unLoadableScheduleStates.results;
            }

            const scheduleDefinitionsSection = (
              <Group direction="vertical" spacing={32}>
                <Box
                  flex={{justifyContent: 'space-between', alignItems: 'flex-end'}}
                  padding={{bottom: 12}}
                  border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
                >
                  <Heading>All schedules</Heading>
                  <SchedulerTimezoneNote schedulerOrError={scheduler} />
                </Box>
                {repositoriesOrError.nodes.map((repository) => (
                  <Group direction="vertical" spacing={12} key={repository.name}>
                    <Subheading>{`${repository.name}@${repository.location.name}`}</Subheading>
                    <SchedulesTable repository={repository} />
                  </Group>
                ))}
              </Group>
            );

            const hasSensors = repositoriesOrError.nodes.some(
              (repository) => repository.sensors.length,
            );
            const unloadableSensors =
              unloadableSensorStatesOrError.__typename === 'JobStates'
                ? unloadableSensorStatesOrError.results
                : [];

            const sensorDefinitionsSection =
              hasSensors || unloadableSensors.length ? (
                <Group direction="vertical" spacing={32}>
                  <Box
                    flex={{justifyContent: 'space-between', alignItems: 'flex-end'}}
                    padding={{bottom: 12}}
                    border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
                  >
                    <Heading>All sensors</Heading>
                  </Box>
                  {repositoriesOrError.nodes.map((repository) =>
                    repository.sensors.length ? (
                      <Group direction="vertical" spacing={12} key={repository.name}>
                        <Subheading>{`${repository.name}@${repository.location.name}`}</Subheading>
                        <SensorsTable
                          repoAddress={{name: repository.name, location: repository.location.name}}
                          sensors={repository.sensors}
                        />
                      </Group>
                    ) : null,
                  )}
                </Group>
              ) : null;

            return (
              <Group direction="vertical" spacing={32}>
                <SchedulerInfo schedulerOrError={scheduler} />
                {scheduleDefinitionsSection}
                {unLoadableSchedules.length > 0 && (
                  <UnLoadableSchedules unLoadableSchedules={unLoadableSchedules} />
                )}
                {sensorDefinitionsSection}
                {unloadableSensors.length > 0 && (
                  <UnloadableSensors sensorStates={unloadableSensors} />
                )}
              </Group>
            );
          }}
        </Loading>
      </div>
    </ScrollContainer>
  );
};

const INSTANCE_JOBS_ROOT_QUERY = gql`
  query InstanceJobsRootQuery {
    repositoriesOrError {
      __typename
      ... on RepositoryConnection {
        nodes {
          id
          ...RepositorySchedulesFragment
        }
      }
      ...PythonErrorFragment
    }
    scheduler {
      ...SchedulerFragment
    }
    unLoadableScheduleStates: scheduleStatesOrError(withNoScheduleDefinition: true) {
      __typename
      ... on ScheduleStates {
        results {
          id
          ...ScheduleStateFragment
        }
      }
      ...PythonErrorFragment
    }
    unloadableSensorStatesOrError {
      ... on JobStates {
        results {
          id
          ...JobStateFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${SCHEDULE_DEFINITION_FRAGMENT}
  ${SCHEDULER_FRAGMENT}
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${REPOSITORY_SCHEDULES_FRAGMENT}
  ${SENSOR_FRAGMENT}
  ${SCHEDULE_STATE_FRAGMENT}
  ${JOB_STATE_FRAGMENT}
`;
