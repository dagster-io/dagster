import {gql, useQuery} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import React from 'react';

import {Loading} from 'src/Loading';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {REPOSITORY_INFO_FRAGMENT} from 'src/RepositoryInformation';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {UnloadableJobs} from 'src/jobs/UnloadableJobs';
import {SCHEDULE_FRAGMENT, SchedulerTimezoneNote} from 'src/schedules/ScheduleUtils';
import {SCHEDULER_FRAGMENT, SchedulerInfo} from 'src/schedules/SchedulerInfo';
import {SchedulesTable} from 'src/schedules/SchedulesTable';
import {InstanceJobsRootQuery} from 'src/schedules/types/InstanceJobsRootQuery';
import {JOB_STATE_FRAGMENT, SENSOR_FRAGMENT} from 'src/sensors/SensorFragment';
import {SensorsTable} from 'src/sensors/SensorsTable';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Page} from 'src/ui/Page';
import {PageHeader} from 'src/ui/PageHeader';
import {Subheading} from 'src/ui/Text';

export const InstanceJobsRoot = () => {
  useDocumentTitle('Scheduler');
  const queryResult = useQuery<InstanceJobsRootQuery>(INSTANCE_JOBS_ROOT_QUERY, {
    variables: {},
    fetchPolicy: 'cache-and-network',
  });

  return (
    <Page>
      <PageHeader text="Scheduler" />
      <Group direction="vertical" spacing={12}>
        <Loading queryResult={queryResult} allowStaleData={true}>
          {(result) => {
            const {scheduler, repositoriesOrError, unloadableJobStatesOrError} = result;

            if (repositoriesOrError.__typename === 'PythonError') {
              return <PythonErrorInfo error={repositoriesOrError} />;
            }
            if (unloadableJobStatesOrError.__typename === 'PythonError') {
              return <PythonErrorInfo error={unloadableJobStatesOrError} />;
            }

            const unloadableJobs = unloadableJobStatesOrError.results;
            const hasSensors = repositoriesOrError.nodes.some(
              (repository) => repository.sensors.length,
            );
            const hasSchedules = repositoriesOrError.nodes.some(
              (repository) => repository.schedules.length,
            );

            const scheduleDefinitionsSection = hasSchedules ? (
              <Group direction="vertical" spacing={12}>
                <Box
                  flex={{justifyContent: 'space-between', alignItems: 'flex-end'}}
                  padding={{bottom: 8}}
                  border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
                >
                  <Subheading>Schedules</Subheading>
                  <SchedulerTimezoneNote schedulerOrError={scheduler} />
                </Box>
                {repositoriesOrError.nodes.map((repository) => (
                  <Group direction="vertical" spacing={12} key={repository.name}>
                    <strong>{`${repository.name}@${repository.location.name}`}</strong>
                    <SchedulesTable
                      repoAddress={{name: repository.name, location: repository.location.name}}
                      schedules={repository.schedules}
                    />
                  </Group>
                ))}
              </Group>
            ) : null;

            const sensorDefinitionsSection = hasSensors ? (
              <Group direction="vertical" spacing={12}>
                <Box
                  flex={{justifyContent: 'space-between', alignItems: 'flex-end'}}
                  padding={{bottom: 12}}
                  border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
                >
                  <Subheading>Sensors</Subheading>
                </Box>
                {repositoriesOrError.nodes.map((repository) =>
                  repository.sensors.length ? (
                    <Group direction="vertical" spacing={12} key={repository.name}>
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
              <Group direction="vertical" spacing={32}>
                <SchedulerInfo schedulerOrError={scheduler} />
                {scheduleDefinitionsSection}
                {sensorDefinitionsSection}
                <UnloadableJobs jobStates={unloadableJobs} />
              </Group>
            );
          }}
        </Loading>
      </Group>
    </Page>
  );
};

const INSTANCE_JOBS_ROOT_QUERY = gql`
  query InstanceJobsRootQuery {
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

  ${REPOSITORY_INFO_FRAGMENT}
  ${SCHEDULE_FRAGMENT}
  ${SCHEDULER_FRAGMENT}
  ${PythonErrorInfo.fragments.PythonErrorFragment}
  ${SENSOR_FRAGMENT}
  ${JOB_STATE_FRAGMENT}
`;
