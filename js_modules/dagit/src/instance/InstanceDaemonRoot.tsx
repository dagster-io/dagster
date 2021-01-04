import {gql, useQuery} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import React from 'react';

import {JOB_STATE_FRAGMENT} from 'src/JobUtils';
import {Loading} from 'src/Loading';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {REPOSITORY_INFO_FRAGMENT} from 'src/RepositoryInformation';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {DaemonList} from 'src/instance/DaemonList';
import {INSTANCE_HEALTH_FRAGMENT} from 'src/instance/InstanceStatusRoot';
import {InstanceDaemonRootQuery} from 'src/instance/types/InstanceDaemonRootQuery';
import {UnloadableSchedules, UnloadableSensors} from 'src/jobs/UnloadableJobs';
import {SCHEDULE_FRAGMENT, SchedulerTimezoneNote} from 'src/schedules/ScheduleUtils';
import {SCHEDULER_FRAGMENT, SchedulerInfo} from 'src/schedules/SchedulerInfo';
import {SchedulesTable} from 'src/schedules/SchedulesTable';
import {SENSOR_FRAGMENT} from 'src/sensors/SensorFragment';
import {SensorsTable} from 'src/sensors/SensorsTable';
import {JobType} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Page} from 'src/ui/Page';
import {PageHeader} from 'src/ui/PageHeader';
import {Subheading} from 'src/ui/Text';

export const InstanceDaemonRoot = () => {
  useDocumentTitle('Daemons');
  const queryResult = useQuery<InstanceDaemonRootQuery>(INSTANCE_DAEMON_ROOT_QUERY, {
    variables: {},
    fetchPolicy: 'cache-and-network',
  });

  return (
    <Page>
      <PageHeader text="Daemons" />
      <Group direction="column" spacing={12}>
        <Loading queryResult={queryResult} allowStaleData={true}>
          {(result) => {
            const {instance, scheduler, repositoriesOrError, unloadableJobStatesOrError} = result;

            if (repositoriesOrError.__typename === 'PythonError') {
              return <PythonErrorInfo error={repositoriesOrError} />;
            }
            if (unloadableJobStatesOrError.__typename === 'PythonError') {
              return <PythonErrorInfo error={unloadableJobStatesOrError} />;
            }

            const unloadableJobs = unloadableJobStatesOrError.results;
            const withSchedules = repositoriesOrError.nodes.filter(
              (repository) => repository.schedules.length,
            );
            const withSensors = repositoriesOrError.nodes.filter(
              (repository) => repository.sensors.length,
            );

            const hasDaemonScheduler =
              scheduler.__typename === 'Scheduler' &&
              scheduler.schedulerClass === 'DagsterDaemonScheduler';

            const daemonStatusSection = (
              <Group direction="column" spacing={16}>
                <Subheading>Daemon statuses</Subheading>
                <DaemonList daemonHealth={instance.daemonHealth} />
              </Group>
            );

            const scheduleDefinitionsSection = withSchedules.length ? (
              <Box padding={{top: 16}}>
                <Group direction="column" spacing={12}>
                  <Box
                    flex={{justifyContent: 'space-between', alignItems: 'flex-end'}}
                    padding={{bottom: 8}}
                    border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
                  >
                    <Subheading>Schedules</Subheading>
                    <SchedulerTimezoneNote schedulerOrError={scheduler} />
                  </Box>
                  {hasDaemonScheduler ? null : <SchedulerInfo schedulerOrError={scheduler} />}
                  {withSchedules.map((repository) => (
                    <Group direction="column" spacing={12} key={repository.name}>
                      <strong>{`${repository.name}@${repository.location.name}`}</strong>
                      <SchedulesTable
                        repoAddress={{name: repository.name, location: repository.location.name}}
                        schedules={repository.schedules}
                      />
                    </Group>
                  ))}
                </Group>
              </Box>
            ) : null;

            const sensorDefinitionsSection = withSensors.length ? (
              <Group direction="column" spacing={12}>
                <Box
                  flex={{justifyContent: 'space-between', alignItems: 'flex-end'}}
                  padding={{bottom: 12}}
                  border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
                >
                  <Subheading>Sensors</Subheading>
                </Box>
                {withSensors.map((repository) =>
                  repository.sensors.length ? (
                    <Group direction="column" spacing={12} key={repository.name}>
                      <strong>{`${repository.name}@${repository.location.name}`}</strong>
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
              <Group direction="column" spacing={32}>
                {daemonStatusSection}
                {scheduleDefinitionsSection}
                {sensorDefinitionsSection}
                <UnloadableSchedules
                  scheduleStates={unloadableJobs.filter(
                    (state) => state.jobType === JobType.SCHEDULE,
                  )}
                />
                <UnloadableSensors
                  sensorStates={unloadableJobs.filter((state) => state.jobType === JobType.SENSOR)}
                />
              </Group>
            );
          }}
        </Loading>
      </Group>
    </Page>
  );
};

const INSTANCE_DAEMON_ROOT_QUERY = gql`
  query InstanceDaemonRootQuery {
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
          schedules {
            id
            ...ScheduleFragment
          }
          sensors {
            id
            ...SensorFragment
          }
        }
      }
      ...PythonErrorFragment
    }
    scheduler {
      ...SchedulerFragment
    }
    unloadableJobStatesOrError {
      ... on JobStates {
        results {
          id
          ...JobStateFragment
        }
      }
      ...PythonErrorFragment
    }
  }

  ${INSTANCE_HEALTH_FRAGMENT}
  ${REPOSITORY_INFO_FRAGMENT}
  ${SCHEDULE_FRAGMENT}
  ${SCHEDULER_FRAGMENT}
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${SENSOR_FRAGMENT}
  ${JOB_STATE_FRAGMENT}
`;
