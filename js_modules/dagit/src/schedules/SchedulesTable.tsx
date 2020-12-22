import {useMutation} from '@apollo/client';
import {
  Button,
  Colors,
  Icon,
  Intent,
  Menu,
  MenuItem,
  Popover,
  PopoverInteractionKind,
  Position,
  Tag,
  Tooltip,
} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {TickTag} from 'src/JobTick';
import {JobRunStatus} from 'src/JobUtils';
import {ReconcileButton} from 'src/schedules/ReconcileButton';
import {
  START_SCHEDULE_MUTATION,
  STOP_SCHEDULE_MUTATION,
  displayScheduleMutationErrors,
} from 'src/schedules/ScheduleMutations';
import {SchedulePartitionStatus} from 'src/schedules/SchedulePartitionStatus';
import {humanCronString} from 'src/schedules/humanCronString';
import {ScheduleFragment} from 'src/schedules/types/ScheduleFragment';
import {StartSchedule} from 'src/schedules/types/StartSchedule';
import {StopSchedule} from 'src/schedules/types/StopSchedule';
import {JobStatus, JobType} from 'src/types/globalTypes';
import {Group} from 'src/ui/Group';
import {SwitchWithoutLabel} from 'src/ui/SwitchWithoutLabel';
import {Table} from 'src/ui/Table';
import {Code} from 'src/ui/Text';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

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
    <Table striped style={{width: '100%'}}>
      <thead>
        <tr>
          <th style={{width: '60px'}}></th>
          <th style={{width: '300px'}}>Schedule Name</th>
          <th style={{width: '150px'}}>Schedule</th>
          <th style={{width: '120px'}}>
            <Group direction="row" spacing={8} alignItems="center">
              Last Tick
              <Tooltip position="top" content={lastTick}>
                <Icon
                  icon={IconNames.INFO_SIGN}
                  iconSize={12}
                  style={{position: 'relative', top: '-2px'}}
                />
              </Tooltip>
            </Group>
          </th>
          <th>
            <Group direction="row" spacing={8} alignItems="center">
              Last Run
              <Tooltip position="top" content={lastRun}>
                <Icon
                  icon={IconNames.INFO_SIGN}
                  iconSize={12}
                  style={{position: 'relative', top: '-2px'}}
                />
              </Tooltip>
            </Group>
          </th>
          <th>
            <Group direction="row" spacing={8} alignItems="center">
              Partition Status
              <Tooltip position="top" content={partitionStatus}>
                <Icon
                  icon={IconNames.INFO_SIGN}
                  iconSize={12}
                  style={{position: 'relative', top: '-2px'}}
                />
              </Tooltip>
            </Group>
          </th>
          <th>Execution Params</th>
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

const errorDisplay = (status: JobStatus, runningScheduleCount: number) => {
  if (status === JobStatus.STOPPED && runningScheduleCount === 0) {
    return null;
  } else if (status === JobStatus.RUNNING && runningScheduleCount === 1) {
    return null;
  }

  const errors = [];
  if (status === JobStatus.RUNNING && runningScheduleCount === 0) {
    errors.push(
      'Schedule is set to be running, but either the scheduler is not configured or the scheduler is not running the schedule',
    );
  } else if (status === JobStatus.STOPPED && runningScheduleCount > 0) {
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
          To resolve, click <ReconcileButton /> or run <Code>dagster schedule up</Code>
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

  const [startSchedule, {loading: toggleOnInFlight}] = useMutation<StartSchedule>(
    START_SCHEDULE_MUTATION,
    {
      onCompleted: displayScheduleMutationErrors,
    },
  );
  const [stopSchedule, {loading: toggleOffInFlight}] = useMutation<StopSchedule>(
    STOP_SCHEDULE_MUTATION,
    {
      onCompleted: displayScheduleMutationErrors,
    },
  );

  const {name, cronSchedule, pipelineName, mode, scheduleState} = schedule;
  const {id, status, ticks, runningCount: runningScheduleCount} = scheduleState;

  const scheduleSelector = {
    repositoryLocationName: repoAddress.location,
    repositoryName: repoAddress.name,
    scheduleName: name,
  };

  const onStatusChange = () => {
    if (status === JobStatus.RUNNING) {
      stopSchedule({
        variables: {scheduleOriginId: id},
      });
    } else {
      startSchedule({
        variables: {scheduleSelector},
      });
    }
  };

  const latestTick = ticks.length > 0 ? ticks[0] : null;

  return (
    <tr key={name}>
      <td>
        <SwitchWithoutLabel
          checked={status === JobStatus.RUNNING}
          large={true}
          disabled={toggleOffInFlight || toggleOnInFlight}
          innerLabelChecked="on"
          innerLabel="off"
          onChange={onStatusChange}
        />
        {errorDisplay(status, runningScheduleCount)}
      </td>
      <td>
        <Group direction="column" spacing={4}>
          <Link to={workspacePathFromAddress(repoAddress, `/schedules/${name}`)}>{name}</Link>
          <Group direction="row" spacing={4} alignItems="center">
            <Icon
              icon="diagram-tree"
              color={Colors.GRAY2}
              iconSize={12}
              style={{position: 'relative', top: '-2px'}}
            />
            <span style={{fontSize: '13px'}}>
              <Link to={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}/`)}>
                {pipelineName}
              </Link>
            </span>
          </Group>
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
        {latestTick ? (
          <TickTag tick={latestTick} jobType={JobType.SCHEDULE} />
        ) : (
          <span style={{color: Colors.GRAY4}}>None</span>
        )}
      </td>
      <td>
        <JobRunStatus jobState={scheduleState} />
      </td>
      <td>
        <SchedulePartitionStatus schedule={schedule} repoAddress={repoAddress} />
      </td>
      <td>
        <Group direction="row" spacing={2} alignItems="center">
          <div>{`Mode: ${mode}`}</div>
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
        </Group>
      </td>
    </tr>
  );
};
