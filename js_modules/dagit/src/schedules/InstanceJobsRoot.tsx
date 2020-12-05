import {gql, useQuery} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import React from 'react';

import {ScrollContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {REPOSITORY_INFO_FRAGMENT} from 'src/RepositoryInformation';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {UnloadableJobs} from 'src/jobs/UnloadableJobs';
import {SCHEDULE_FRAGMENT, SchedulerTimezoneNote} from 'src/schedules/ScheduleUtils';
import {SCHEDULER_FRAGMENT, SchedulerInfo} from 'src/schedules/SchedulerInfo';
import {SchedulesTable} from 'src/schedules/SchedulesRoot';
import {InstanceJobsRootQuery} from 'src/schedules/types/InstanceJobsRootQuery';
import {JOB_STATE_FRAGMENT, SENSOR_FRAGMENT} from 'src/sensors/SensorFragment';
import {SensorsTable} from 'src/sensors/SensorsTable';
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
              <Group direction="vertical" spacing={32}>
                <Box
                  flex={{justifyContent: 'space-between', alignItems: 'flex-end'}}
                  padding={{bottom: 12}}
                  border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
                >
                  <Heading>Schedules</Heading>
                  <SchedulerTimezoneNote schedulerOrError={scheduler} />
                </Box>
                {repositoriesOrError.nodes.map((repository) => (
                  <Group direction="vertical" spacing={12} key={repository.name}>
                    <Subheading>{`${repository.name}@${repository.location.name}`}</Subheading>
                    <SchedulesTable repository={repository} />
                  </Group>
                ))}
              </Group>
            ) : null;

            const sensorDefinitionsSection = hasSensors ? (
              <Group direction="vertical" spacing={32}>
                <Box
                  flex={{justifyContent: 'space-between', alignItems: 'flex-end'}}
                  padding={{bottom: 12}}
                  border={{side: 'bottom', width: 1, color: Colors.LIGHT_GRAY3}}
                >
                  <Heading>Sensors</Heading>
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
                {sensorDefinitionsSection}
                <UnloadableJobs jobStates={unloadableJobs} />
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
