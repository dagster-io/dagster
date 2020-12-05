import {useMutation, gql} from '@apollo/client';
import {
  Button,
  Colors,
  Intent,
  Menu,
  MenuItem,
  Popover,
  PopoverInteractionKind,
  Position,
  Switch,
  Tag,
  Tooltip,
} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {showCustomAlert} from 'src/CustomAlertProvider';
import {PythonErrorInfo} from 'src/PythonErrorInfo';
import {assertUnreachable} from 'src/Util';
import {RunStatus} from 'src/runs/RunStatusDots';
import {DagsterTag} from 'src/runs/RunTag';
import {titleForRun} from 'src/runs/RunUtils';
import {ReconcileButton} from 'src/schedules/ReconcileButton';
import {humanCronString} from 'src/schedules/humanCronString';
import {
  ScheduleFragment,
  ScheduleFragment_scheduleState_ticks_tickSpecificData,
} from 'src/schedules/types/ScheduleFragment';
import {
  StartSchedule,
  StartSchedule_startSchedule_PythonError,
} from 'src/schedules/types/StartSchedule';
import {
  StopSchedule,
  StopSchedule_stopRunningSchedule_PythonError,
} from 'src/schedules/types/StopSchedule';
import {ScheduleStatus, JobTickStatus} from 'src/types/globalTypes';
import {Code} from 'src/ui/Text';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

type TickSpecificData = ScheduleFragment_scheduleState_ticks_tickSpecificData | null;

const NUM_RUNS_TO_DISPLAY = 10;

const errorDisplay = (status: ScheduleStatus, runningScheduleCount: number) => {
  if (status === ScheduleStatus.STOPPED && runningScheduleCount === 0) {
    return null;
  } else if (status === ScheduleStatus.RUNNING && runningScheduleCount === 1) {
    return null;
  }

  const errors = [];
  if (status === ScheduleStatus.RUNNING && runningScheduleCount === 0) {
    errors.push(
      'Schedule is set to be running, but either the scheduler is not configured or the scheduler is not running the schedule',
    );
  } else if (status === ScheduleStatus.STOPPED && runningScheduleCount > 0) {
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

export const displayScheduleMutationErrors = (data: StartSchedule | StopSchedule) => {
  let error:
    | StartSchedule_startSchedule_PythonError
    | StopSchedule_stopRunningSchedule_PythonError
    | null = null;

  if ('startSchedule' in data && data.startSchedule.__typename === 'PythonError') {
    error = data.startSchedule;
  } else if (
    'stopRunningSchedule' in data &&
    data.stopRunningSchedule.__typename === 'PythonError'
  ) {
    error = data.stopRunningSchedule;
  }

  if (error) {
    showCustomAlert({
      title: 'Schedule Response',
      body: (
        <>
          <PythonErrorInfo error={error} />
        </>
      ),
    });
  }
};

export const ScheduleRow: React.FC<{
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

  const scheduleSelector = {
    repositoryLocationName: repoAddress.location,
    repositoryName: repoAddress.name,
    scheduleName: name,
  };

  const displayName = (
    <Link to={workspacePathFromAddress(repoAddress, `/schedules/${name}`)}>{name}</Link>
  );

  if (!scheduleState) {
    return (
      <tr key={name}>
        <td>{displayName}</td>
        <td>
          <Link to={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}/`)}>
            {pipelineName}
          </Link>
        </td>
        <td
          style={{
            maxWidth: 150,
          }}
        >
          {cronSchedule ? (
            <Tooltip position={'bottom'} content={cronSchedule}>
              {humanCronString(cronSchedule)}
            </Tooltip>
          ) : (
            <div>-</div>
          )}
        </td>
        <td
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            flex: 1,
          }}
        >
          <div style={{flex: 1}}>
            <div>{`Mode: ${mode}`}</div>
          </div>
        </td>
      </tr>
    );
  }

  const {status, runningScheduleCount, ticks, runs, runsCount, scheduleOriginId} = scheduleState;

  const latestTick = ticks.length > 0 ? ticks[0] : null;

  return (
    <tr key={name}>
      <td style={{maxWidth: '64px'}}>
        <Switch
          checked={status === ScheduleStatus.RUNNING}
          large={true}
          disabled={toggleOffInFlight || toggleOnInFlight}
          innerLabelChecked="on"
          innerLabel="off"
          onChange={() => {
            if (status === ScheduleStatus.RUNNING) {
              stopSchedule({
                variables: {scheduleOriginId},
              });
            } else {
              startSchedule({
                variables: {scheduleSelector},
              });
            }
          }}
        />

        {errorDisplay(status, runningScheduleCount)}
      </td>
      <td>{displayName}</td>
      <td>
        <Link to={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}/`)}>
          {pipelineName}
        </Link>
      </td>
      <td
        style={{
          maxWidth: 150,
        }}
      >
        {cronSchedule ? (
          <Tooltip position={'bottom'} content={cronSchedule}>
            {humanCronString(cronSchedule)}
          </Tooltip>
        ) : (
          <div>-</div>
        )}
      </td>
      <td style={{maxWidth: 100}}>
        {latestTick ? (
          <TickTag status={latestTick.status} eventSpecificData={latestTick.tickSpecificData} />
        ) : (
          <span style={{color: Colors.GRAY4}}>None</span>
        )}
      </td>
      <td>
        <div style={{display: 'flex'}}>
          {runs.map((run) => {
            const [partition] = run.tags
              .filter((tag) => tag.key === DagsterTag.Partition)
              .map((tag) => tag.value);
            const runLabel = partition ? (
              <>
                <div>Run id: {titleForRun(run)}</div>
                <div>Partition: {partition}</div>
              </>
            ) : (
              titleForRun(run)
            );
            return (
              <div
                style={{
                  cursor: 'pointer',
                  marginRight: '4px',
                }}
                key={run.runId}
              >
                <Link to={`/instance/runs/${run.runId}`}>
                  <Tooltip
                    position={'top'}
                    content={runLabel}
                    wrapperTagName="div"
                    targetTagName="div"
                  >
                    <RunStatus status={run.status} />
                  </Tooltip>
                </Link>
              </div>
            );
          })}
        </div>
        {runsCount > NUM_RUNS_TO_DISPLAY && (
          <Link
            to={workspacePathFromAddress(repoAddress, `/schedules/${name}`)}
            style={{verticalAlign: 'top'}}
          >
            {' '}
            +{runsCount - NUM_RUNS_TO_DISPLAY} more
          </Link>
        )}
      </td>
      <td>
        <div style={{display: 'flex', alignItems: 'center'}}>
          <div>{`Mode: ${mode}`}</div>
          <Popover
            content={
              <Menu>
                {schedule.partitionSet?.name ? (
                  <MenuItem
                    text="View Partition History..."
                    icon="multi-select"
                    target="_blank"
                    href={workspacePathFromAddress(
                      repoAddress,
                      `/pipelines/${pipelineName}/partitions`,
                    )}
                  />
                ) : null}
              </Menu>
            }
            position="bottom"
          >
            <Button small minimal icon="chevron-down" style={{marginLeft: '4px'}} />
          </Popover>
        </div>
      </td>
    </tr>
  );
};

export const ScheduleRowHeader: React.FunctionComponent<{
  schedule: ScheduleFragment;
}> = ({schedule}) => {
  if (!schedule.scheduleState) {
    return (
      <tr>
        <th>Schedule Name</th>
        <th>Pipeline</th>
        <th>Schedule</th>
        <th>Execution Params</th>
      </tr>
    );
  } else {
    return (
      <tr>
        <th></th>
        <th>Schedule Name</th>
        <th>Pipeline</th>
        <th>Schedule</th>
        <th>Last Tick</th>
        <th>Latest Runs</th>
        <th>Execution Params</th>
      </tr>
    );
  }
};

export const TickTag: React.FunctionComponent<{
  status: JobTickStatus;
  eventSpecificData: TickSpecificData;
}> = ({status, eventSpecificData}) => {
  switch (status) {
    case JobTickStatus.STARTED:
      return (
        <Tag minimal={true} intent={Intent.PRIMARY}>
          Started
        </Tag>
      );
    case JobTickStatus.SUCCESS:
      if (!eventSpecificData || eventSpecificData.__typename !== 'ScheduleTickSuccessData') {
        return (
          <Tag minimal={true} intent={Intent.SUCCESS}>
            Success
          </Tag>
        );
      } else {
        return (
          <a
            href={`/instance/runs/${eventSpecificData.run?.runId}`}
            style={{textDecoration: 'none'}}
          >
            <Tag minimal={true} intent={Intent.SUCCESS} interactive={true}>
              Success
            </Tag>
          </a>
        );
      }
    case JobTickStatus.SKIPPED:
      return (
        <Tag minimal={true} intent={Intent.WARNING}>
          Skipped
        </Tag>
      );
    case JobTickStatus.FAILURE:
      if (!eventSpecificData || eventSpecificData.__typename !== 'ScheduleTickFailureData') {
        return (
          <Tag minimal={true} intent={Intent.DANGER}>
            Failure
          </Tag>
        );
      } else {
        return (
          <LinkButton
            onClick={() =>
              showCustomAlert({
                title: 'Schedule Response',
                body: <PythonErrorInfo error={eventSpecificData.error} />,
              })
            }
          >
            <Tag minimal={true} intent={Intent.DANGER} interactive={true}>
              Failure
            </Tag>
          </LinkButton>
        );
      }
    default:
      return assertUnreachable(status);
  }
};

export const START_SCHEDULE_MUTATION = gql`
  mutation StartSchedule($scheduleSelector: ScheduleSelector!) {
    startSchedule(scheduleSelector: $scheduleSelector) {
      __typename
      ... on ScheduleStateResult {
        scheduleState {
          __typename
          id
          runningScheduleCount
          status
        }
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
`;

export const STOP_SCHEDULE_MUTATION = gql`
  mutation StopSchedule($scheduleOriginId: String!) {
    stopRunningSchedule(scheduleOriginId: $scheduleOriginId) {
      __typename
      ... on ScheduleStateResult {
        scheduleState {
          __typename
          id
          runningScheduleCount
          status
        }
      }
      ... on PythonError {
        message
        stack
      }
    }
  }
`;

const LinkButton = styled.button`
  background: inherit;
  border: none;
  cursor: pointer;
  font-size: inherit;
  text-decoration: none;
  padding: 0;
`;
