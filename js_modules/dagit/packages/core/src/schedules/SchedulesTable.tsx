import {Box, Button, Colors, Icon, Menu, Popover, Table, Tag, Tooltip} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {TickTag} from '../instigation/InstigationTick';
import {InstigatedRunStatus} from '../instigation/InstigationUtils';
import {PipelineReference} from '../pipelines/PipelineReference';
import {InstigationStatus, InstigationType} from '../types/globalTypes';
import {MenuLink} from '../ui/MenuLink';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {SchedulePartitionStatus} from './SchedulePartitionStatus';
import {ScheduleSwitch} from './ScheduleSwitch';
import {TimestampDisplay} from './TimestampDisplay';
import {humanCronString} from './humanCronString';
import {ScheduleFragment} from './types/ScheduleFragment';

export const SchedulesTable: React.FC<{
  schedules: ScheduleFragment[];
  repoAddress: RepoAddress;
}> = ({repoAddress, schedules}) => {
  const lastTick = 'Status of the last tick: One of `Started`, `Skipped`, `Requested`, `Failed`';
  const lastRun = 'The status of the last run requested by this schedule';
  const partitionStatus = (
    <div style={{width: 300}}>
      <p>The status of each partition in the partition set associated with this schedule.</p>
      <p>
        Partitions have a `Success` status if the last run for that partition completed
        successfully.
      </p>
      <p>Partititons have a `Missing` status if no run has been executed for that partition.</p>
    </div>
  );

  return (
    <Table>
      <thead>
        <tr>
          <th style={{width: '60px'}}></th>
          <th>Schedule name</th>
          <th style={{width: '15%'}}>Schedule</th>
          <th style={{width: '10%'}}>Next tick</th>
          <th style={{width: '10%'}}>
            <Box flex={{gap: 8, alignItems: 'end'}}>
              Last tick
              <Tooltip position="top" content={lastTick}>
                <Icon name="info" color={Colors.Gray400} />
              </Tooltip>
            </Box>
          </th>
          <th style={{width: 130}}>
            <Box flex={{gap: 8, alignItems: 'end'}}>
              Last run
              <Tooltip position="top" content={lastRun}>
                <Icon name="info" color={Colors.Gray400} />
              </Tooltip>
            </Box>
          </th>
          <th style={{width: '30%'}}>
            <Box flex={{gap: 8, alignItems: 'end'}}>
              Partition Set
              <Tooltip position="top" content={partitionStatus}>
                <Icon name="info" color={Colors.Gray400} />
              </Tooltip>
            </Box>
          </th>
          <th style={{width: 80}} />
        </tr>
      </thead>
      <tbody>
        {schedules.map((schedule) => (
          <ScheduleRow repoAddress={repoAddress} schedule={schedule} key={schedule.name} />
        ))}
      </tbody>
    </Table>
  );
};

const errorDisplay = (status: InstigationStatus, runningScheduleCount: number) => {
  if (status === InstigationStatus.STOPPED && runningScheduleCount === 0) {
    return null;
  } else if (status === InstigationStatus.RUNNING && runningScheduleCount === 1) {
    return null;
  }

  const errors = [];
  if (status === InstigationStatus.RUNNING && runningScheduleCount === 0) {
    errors.push(
      'Schedule is set to be running, but either the scheduler is not configured or the scheduler is not running the schedule',
    );
  } else if (status === InstigationStatus.STOPPED && runningScheduleCount > 0) {
    errors.push('Schedule is set to be stopped, but the scheduler is still running the schedule');
  }

  if (runningScheduleCount > 0) {
    errors.push('Duplicate cron job for schedule found.');
  }

  return (
    <Popover
      interactionKind="hover"
      popoverClassName="bp3-popover-content-sizing"
      position="right"
      content={
        <Box flex={{direction: 'column', gap: 8}} padding={12}>
          <strong>There are errors with this schedule.</strong>
          <div>Errors:</div>
          <ul>
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </Box>
      }
    >
      <Tag fill interactive intent="danger">
        Error
      </Tag>
    </Popover>
  );
};

const ScheduleRow: React.FC<{
  schedule: ScheduleFragment;
  repoAddress: RepoAddress;
}> = (props) => {
  const {repoAddress, schedule} = props;
  const repo = useRepository(repoAddress);
  const isJob = isThisThingAJob(repo, schedule.pipelineName);

  const {
    name,
    cronSchedule,
    executionTimezone,
    futureTicks,
    pipelineName,
    scheduleState,
  } = schedule;
  const {status, ticks, runningCount: runningScheduleCount} = scheduleState;

  const latestTick = ticks.length > 0 ? ticks[0] : null;

  return (
    <tr key={name}>
      <td>
        <Box flex={{direction: 'column', gap: 4}}>
          <ScheduleSwitch repoAddress={repoAddress} schedule={schedule} />
          {errorDisplay(status, runningScheduleCount)}
        </Box>
      </td>
      <td>
        <Box flex={{direction: 'column', gap: 4}}>
          <span style={{fontWeight: 500}}>
            <Link to={workspacePathFromAddress(repoAddress, `/schedules/${name}`)}>{name}</Link>
          </span>
          <PipelineReference
            showIcon
            size="small"
            pipelineName={pipelineName}
            pipelineHrefContext={repoAddress}
            isJob={isJob}
          />
        </Box>
      </td>
      <td>
        {cronSchedule ? (
          <Tooltip position="bottom" content={cronSchedule}>
            <span>{humanCronString(cronSchedule, executionTimezone || 'UTC')}</span>
          </Tooltip>
        ) : (
          <span style={{color: Colors.Gray300}}>None</span>
        )}
      </td>
      <td>
        {futureTicks.results.length && status === InstigationStatus.RUNNING ? (
          <TimestampDisplay
            timestamp={futureTicks.results[0].timestamp}
            timezone={executionTimezone}
            timeFormat={{showSeconds: false, showTimezone: true}}
          />
        ) : (
          <span style={{color: Colors.Gray300}}>None</span>
        )}
      </td>
      <td>
        {latestTick ? (
          <TickTag tick={latestTick} instigationType={InstigationType.SCHEDULE} />
        ) : (
          <span style={{color: Colors.Gray300}}>None</span>
        )}
      </td>
      <td>
        <InstigatedRunStatus instigationState={scheduleState} />
      </td>
      <td>
        {schedule.partitionSet ? (
          <SchedulePartitionStatus schedule={schedule} repoAddress={repoAddress} />
        ) : (
          <div style={{color: Colors.Gray300}}>None</div>
        )}
      </td>
      <td>
        {schedule.partitionSet ? (
          <Popover
            content={
              <Menu>
                <MenuLink
                  text="View Partition History..."
                  icon="dynamic_feed"
                  target="_blank"
                  to={workspacePathFromAddress(
                    repoAddress,
                    `/${isJob ? 'jobs' : 'pipelines'}/${pipelineName}/partitions`,
                  )}
                />
                <MenuLink
                  text="Launch Partition Backfill..."
                  icon="add_circle"
                  target="_blank"
                  to={workspacePathFromAddress(
                    repoAddress,
                    `/${isJob ? 'jobs' : 'pipelines'}/${pipelineName}/partitions`,
                  )}
                />
              </Menu>
            }
            position="bottom-left"
          >
            <Button icon={<Icon name="expand_more" />} />
          </Popover>
        ) : null}
      </td>
    </tr>
  );
};
