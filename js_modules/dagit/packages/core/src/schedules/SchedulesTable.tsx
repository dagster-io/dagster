import {
  Button,
  Colors,
  Intent,
  Menu,
  MenuItem,
  Popover,
  PopoverInteractionKind,
  Position,
  Tag,
} from '@blueprintjs/core';
import {Tooltip2 as Tooltip} from '@blueprintjs/popover2';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {TickTag} from '../instigation/InstigationTick';
import {InstigatedRunStatus} from '../instigation/InstigationUtils';
import {PipelineReference} from '../pipelines/PipelineReference';
import {InstigationStatus, InstigationType} from '../types/globalTypes';
import {ColorsWIP} from '../ui/Colors';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';
import {Table} from '../ui/Table';
import {Code} from '../ui/Text';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {ReconcileButton} from './ReconcileButton';
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
          <th style={{minWidth: '300px'}}>Schedule Name</th>
          <th style={{minWidth: '150px'}}>Schedule</th>
          <th style={{width: '160px'}}>Next Tick</th>
          <th style={{width: '120px'}}>
            <Group direction="row" spacing={8} alignItems="center">
              Last Tick
              <Tooltip position="top" content={lastTick}>
                <IconWIP name="info" color={ColorsWIP.Gray400} />
              </Tooltip>
            </Group>
          </th>
          <th>
            <Group direction="row" spacing={8} alignItems="center">
              Last Run
              <Tooltip position="top" content={lastRun}>
                <IconWIP name="info" color={ColorsWIP.Gray400} />
              </Tooltip>
            </Group>
          </th>
          <th>
            <Group direction="row" spacing={8} alignItems="center">
              Partition
              <Tooltip position="top" content={partitionStatus}>
                <IconWIP name="info" color={ColorsWIP.Gray400} />
              </Tooltip>
            </Group>
          </th>
          <th />
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

const errorDisplay = (
  status: InstigationStatus,
  runningScheduleCount: number,
  repoAddress: RepoAddress,
) => {
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
      interactionKind={PopoverInteractionKind.CLICK}
      popoverClassName="bp3-popover-content-sizing"
      position={Position.RIGHT}
      fill={true}
    >
      <Tag fill={true} interactive={true} intent={Intent.DANGER}>
        Error
      </Tag>
      <div>
        <h3>There are errors with this schedule.</h3>

        <p>Errors:</p>
        <ul>
          {errors.map((error, index) => (
            <li key={index}>{error}</li>
          ))}
        </ul>

        <p>
          To resolve, click <ReconcileButton repoAddress={repoAddress} /> or run{' '}
          <Code>dagster schedule up</Code>
        </p>
      </div>
    </Popover>
  );
};

const ScheduleRow: React.FC<{
  schedule: ScheduleFragment;
  repoAddress: RepoAddress;
}> = (props) => {
  const {repoAddress, schedule} = props;

  const {
    name,
    cronSchedule,
    executionTimezone,
    futureTicks,
    pipelineName,
    mode,
    scheduleState,
  } = schedule;
  const {status, ticks, runningCount: runningScheduleCount} = scheduleState;

  const latestTick = ticks.length > 0 ? ticks[0] : null;

  return (
    <tr key={name}>
      <td>
        <ScheduleSwitch repoAddress={repoAddress} schedule={schedule} />
        {errorDisplay(status, runningScheduleCount, repoAddress)}
      </td>
      <td>
        <Group direction="column" spacing={4}>
          <span style={{fontWeight: 500}}>
            <Link to={workspacePathFromAddress(repoAddress, `/schedules/${name}`)}>{name}</Link>
          </span>
          <PipelineReference
            showIcon
            fontSize={13}
            pipelineName={pipelineName}
            pipelineHrefContext={repoAddress}
            mode={mode}
          />
        </Group>
      </td>
      <td>
        {cronSchedule ? (
          <Tooltip position={'bottom'} content={cronSchedule}>
            {humanCronString(cronSchedule)}
          </Tooltip>
        ) : (
          <span style={{color: Colors.GRAY4}}>None</span>
        )}
      </td>
      <td>
        {futureTicks.results.length && status === InstigationStatus.RUNNING ? (
          <TimestampDisplay
            timestamp={futureTicks.results[0].timestamp}
            timezone={executionTimezone}
          />
        ) : (
          <span style={{color: Colors.GRAY4}}>None</span>
        )}
      </td>
      <td>
        {latestTick ? (
          <TickTag tick={latestTick} instigationType={InstigationType.SCHEDULE} />
        ) : (
          <span style={{color: Colors.GRAY4}}>None</span>
        )}
      </td>
      <td>
        <InstigatedRunStatus instigationState={scheduleState} />
      </td>
      <td>
        {schedule.partitionSet ? (
          <SchedulePartitionStatus schedule={schedule} repoAddress={repoAddress} />
        ) : (
          <div style={{color: Colors.GRAY4}}>None</div>
        )}
      </td>
      <td>
        {schedule.partitionSet ? (
          <Popover
            content={
              <Menu>
                <MenuItem
                  text="View Partition History..."
                  icon="multi-select"
                  target="_blank"
                  href={workspacePathFromAddress(
                    repoAddress,
                    `/pipelines/${pipelineName}/partitions`,
                  )}
                />
                <MenuItem
                  text="Launch Partition Backfill..."
                  icon="add"
                  target="_blank"
                  href={workspacePathFromAddress(
                    repoAddress,
                    `/pipelines/${pipelineName}/partitions`,
                  )}
                />
              </Menu>
            }
            position="bottom"
          >
            <Button small minimal icon="chevron-down" style={{marginLeft: '4px'}} />
          </Popover>
        ) : null}
      </td>
    </tr>
  );
};
