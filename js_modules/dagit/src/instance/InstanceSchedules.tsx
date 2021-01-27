import {QueryResult} from '@apollo/client';
import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';

import {PythonErrorInfo} from 'src/app/PythonErrorInfo';
import {InstanceHealthQuery} from 'src/instance/types/InstanceHealthQuery';
import {UnloadableSchedules} from 'src/jobs/UnloadableJobs';
import {SchedulerTimezoneNote} from 'src/schedules/ScheduleUtils';
import {SchedulerInfo} from 'src/schedules/SchedulerInfo';
import {SchedulesTable} from 'src/schedules/SchedulesTable';
import {JobType} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {Loading} from 'src/ui/Loading';
import {Subheading} from 'src/ui/Text';
import {buildRepoAddress} from 'src/workspace/buildRepoAddress';

interface Props {
  queryData: QueryResult<InstanceHealthQuery>;
}

export const InstanceSchedules = React.memo((props: Props) => {
  const {queryData} = props;

  return (
    <Loading queryResult={queryData} allowStaleData={true}>
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

        const scheduleDefinitionsSection = withSchedules.length ? (
          <Group direction="column" spacing={32}>
            <Group direction="column" spacing={12}>
              <SchedulerTimezoneNote schedulerOrError={scheduler} />
              <SchedulerInfo schedulerOrError={scheduler} daemonHealth={instance.daemonHealth} />
            </Group>
            {withSchedules.map((repository) => (
              <Group direction="column" spacing={12} key={repository.name}>
                <Subheading>{`${repository.name}@${repository.location.name}`}</Subheading>
                <SchedulesTable
                  repoAddress={buildRepoAddress(repository.name, repository.location.name)}
                  schedules={repository.schedules}
                />
              </Group>
            ))}
          </Group>
        ) : null;

        const unloadableSchedules = unloadableJobs.filter(
          (state) => state.jobType === JobType.SCHEDULE,
        );

        const unloadableSchedulesSection = unloadableSchedules.length ? (
          <UnloadableSchedules scheduleStates={unloadableSchedules} />
        ) : null;

        if (!scheduleDefinitionsSection && !unloadableSchedulesSection) {
          return (
            <Box margin={{top: 32}}>
              <NonIdealState
                icon="time"
                title="No schedules found"
                description={
                  <p>
                    This instance does not have any schedules defined. Visit the{' '}
                    <a
                      href="https://docs.dagster.io/overview/schedules-sensors/schedules"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      scheduler documentation
                    </a>{' '}
                    for more information about scheduling pipeline runs in Dagster.
                  </p>
                }
              />
            </Box>
          );
        }

        return (
          <Group direction="column" spacing={32}>
            {scheduleDefinitionsSection}
            {unloadableSchedulesSection}
          </Group>
        );
      }}
    </Loading>
  );
});
