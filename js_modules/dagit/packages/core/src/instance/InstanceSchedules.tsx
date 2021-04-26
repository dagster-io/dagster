import {QueryResult} from '@apollo/client';
import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {UnloadableSchedules} from '../jobs/UnloadableJobs';
import {Group, Box} from '../main';
import {SchedulerTimezoneNote} from '../schedules/ScheduleUtils';
import {SchedulerInfo} from '../schedules/SchedulerInfo';
import {SchedulesTable} from '../schedules/SchedulesTable';
import {JobType} from '../types/globalTypes';
import {Loading} from '../ui/Loading';
import {Subheading} from '../ui/Text';
import {buildRepoPath, buildRepoAddress} from '../workspace/buildRepoAddress';

import {InstanceHealthQuery} from './types/InstanceHealthQuery';

interface Props {
  queryData: QueryResult<InstanceHealthQuery>;
}

export const InstanceSchedules = React.memo((props: Props) => {
  const {queryData} = props;
  return (
    <Loading queryResult={queryData} allowStaleData={true}>
      {(data) => <AllSchedules data={data} />}
    </Loading>
  );
});

const AllSchedules: React.FC<{data: InstanceHealthQuery}> = ({data}) => {
  const {instance, scheduler, repositoriesOrError, unloadableJobStatesOrError} = data;

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

  const loadedSchedulesSection = withSchedules.length ? (
    <Group direction="column" spacing={32}>
      <Group direction="column" spacing={12}>
        <SchedulerTimezoneNote schedulerOrError={scheduler} />
        <SchedulerInfo schedulerOrError={scheduler} daemonHealth={instance.daemonHealth} />
      </Group>
      {withSchedules.map((repository) => (
        <Group direction="column" spacing={8} key={repository.name}>
          <Subheading>{`${buildRepoPath(repository.name, repository.location.name)}`}</Subheading>
          <SchedulesTable
            repoAddress={buildRepoAddress(repository.name, repository.location.name)}
            schedules={repository.schedules}
          />
        </Group>
      ))}
    </Group>
  ) : null;

  const unloadableSchedules = unloadableJobs.filter((state) => state.jobType === JobType.SCHEDULE);

  const unloadableSchedulesSection = unloadableSchedules.length ? (
    <UnloadableSchedules scheduleStates={unloadableSchedules} />
  ) : null;

  if (!loadedSchedulesSection && !unloadableSchedulesSection) {
    return (
      <Box margin={{top: 32}}>
        <NonIdealState
          icon="time"
          title="No schedules found"
          description={
            <div>
              This instance does not have any schedules defined. Visit the{' '}
              <a
                href="https://docs.dagster.io/overview/schedules-sensors/schedules"
                target="_blank"
                rel="noreferrer"
              >
                scheduler documentation
              </a>{' '}
              for more information about scheduling pipeline runs in Dagster.
            </div>
          }
        />
      </Box>
    );
  }

  return (
    <Group direction="column" spacing={32}>
      {loadedSchedulesSection}
      {unloadableSchedulesSection}
    </Group>
  );
};
