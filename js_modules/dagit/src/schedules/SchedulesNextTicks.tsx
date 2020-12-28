import * as React from 'react';
import {Link} from 'react-router-dom';

import {TimestampDisplay} from 'src/schedules/TimestampDisplay';
import {ScheduleFragment} from 'src/schedules/types/ScheduleFragment';
import {JobStatus} from 'src/types/globalTypes';
import {Group} from 'src/ui/Group';
import {Table} from 'src/ui/Table';
import {Subheading} from 'src/ui/Text';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

interface ScheduleTick {
  schedule: ScheduleFragment;
  timestamp: number;
}

export const SchedulesNextTicks: React.FC<{
  repoAddress: RepoAddress;
  schedules: ScheduleFragment[];
}> = ({repoAddress, schedules}) => {
  const futureTickSchedules = schedules.filter(
    (schedule) =>
      schedule.futureTicks.results.length && schedule.scheduleState.status === JobStatus.RUNNING,
  );

  const minMaxTimestamp = Math.min(
    ...futureTickSchedules.map(
      (schedule) => schedule.futureTicks.results[schedule.futureTicks.results.length - 1].timestamp,
    ),
  );

  const nextTicks: ScheduleTick[] = [];
  futureTickSchedules.forEach((schedule) => {
    schedule.futureTicks.results.forEach((tick) => {
      if (tick.timestamp <= minMaxTimestamp) {
        nextTicks.push({schedule, timestamp: tick.timestamp});
      }
    });
  });

  nextTicks.sort((a, b) => a.timestamp - b.timestamp);

  return (
    <Group direction="column" spacing={12}>
      <Subheading>Upcoming Ticks</Subheading>
      <Table style={{width: '100%'}}>
        <thead>
          <tr>
            <th style={{width: '60px'}}>Timestamp</th>
            <th style={{width: '300px'}}>Schedule</th>
          </tr>
        </thead>
        <tbody>
          {nextTicks.map(({schedule, timestamp}) => (
            <tr key={`${schedule.id}:${timestamp}`}>
              <td>
                <TimestampDisplay timestamp={timestamp} timezone={schedule.executionTimezone} />
              </td>
              <td>
                <Link to={workspacePathFromAddress(repoAddress, `/schedules/${schedule.name}`)}>
                  {schedule.name}
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Group>
  );
};
