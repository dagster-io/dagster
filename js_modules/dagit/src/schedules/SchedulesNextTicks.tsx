import {NonIdealState} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {TimestampDisplay} from 'src/schedules/TimestampDisplay';
import {RepositorySchedulesFragment} from 'src/schedules/types/RepositorySchedulesFragment';
import {ScheduleFragment} from 'src/schedules/types/ScheduleFragment';
import {JobStatus} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {Table} from 'src/ui/Table';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

interface ScheduleTick {
  schedule: ScheduleFragment;
  timestamp: number;
  repoAddress: RepoAddress;
}

export const SchedulesNextTicks: React.FC<{
  repos: RepositorySchedulesFragment[];
}> = React.memo(({repos}) => {
  const nextTicks: ScheduleTick[] = [];

  repos.forEach((repo) => {
    const {schedules} = repo;
    const repoAddress = {
      name: repo.name,
      location: repo.location.name,
    };

    const futureTickSchedules = schedules.filter(
      (schedule) =>
        schedule.futureTicks.results.length && schedule.scheduleState.status === JobStatus.RUNNING,
    );

    const minMaxTimestamp = Math.min(
      ...futureTickSchedules.map(
        (schedule) =>
          schedule.futureTicks.results[schedule.futureTicks.results.length - 1].timestamp,
      ),
    );

    futureTickSchedules.forEach((schedule) => {
      schedule.futureTicks.results.forEach((tick) => {
        if (tick.timestamp <= minMaxTimestamp) {
          nextTicks.push({schedule, timestamp: tick.timestamp, repoAddress});
        }
      });
    });
  });

  nextTicks.sort((a, b) => a.timestamp - b.timestamp);

  if (!nextTicks.length) {
    return (
      <Box margin={{top: 32}}>
        <NonIdealState
          title="No scheduled ticks"
          description="There are no running schedules. Start a schedule to see scheduled ticks."
        />
      </Box>
    );
  }

  return (
    <Table>
      <thead>
        <tr>
          <th style={{width: '200px'}}>Timestamp</th>
          <th style={{width: '30%'}}>Schedule</th>
          <th>Pipeline</th>
        </tr>
      </thead>
      <tbody>
        {nextTicks.map(({schedule, timestamp, repoAddress}) => (
          <tr key={`${schedule.id}:${timestamp}`}>
            <td>
              <TimestampDisplay
                timestamp={timestamp}
                timezone={schedule.executionTimezone}
                format="MMM D, h:mm A z"
              />
            </td>
            <td>
              <Link to={workspacePathFromAddress(repoAddress, `/schedules/${schedule.name}`)}>
                {schedule.name}
              </Link>
            </td>
            <td>
              <Link
                to={workspacePathFromAddress(repoAddress, `/pipelines/${schedule.pipelineName}/`)}
              >
                {schedule.pipelineName}
              </Link>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
});
