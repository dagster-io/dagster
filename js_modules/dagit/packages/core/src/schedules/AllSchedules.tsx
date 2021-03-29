import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';

import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {InstanceHealthFragment} from '../instance/types/InstanceHealthFragment';
import {UnloadableSchedules} from '../jobs/UnloadableJobs';
import {JobType} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {Group} from '../ui/Group';
import {Subheading} from '../ui/Text';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

import {SchedulerTimezoneNote} from './ScheduleUtils';
import {SchedulerInfo} from './SchedulerInfo';
import {SchedulesTable} from './SchedulesTable';
import {AllSchedulesRepositoriesFragment} from './types/AllSchedulesRepositoriesFragment';
import {AllSchedulesUnloadablesFragment} from './types/AllSchedulesUnloadablesFragment';
import {SchedulerFragment} from './types/SchedulerFragment';

interface Props {
  instance: InstanceHealthFragment;
  scheduler: SchedulerFragment;
  repositoriesOrError: AllSchedulesRepositoriesFragment;
  unloadableJobStatesOrError: AllSchedulesUnloadablesFragment;
}

export const AllSchedules: React.FC<Props> = (props) => {
  const {instance, scheduler, repositoriesOrError, unloadableJobStatesOrError} = props;

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
          <Subheading>{`${repository.name}@${repository.location.name}`}</Subheading>
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
