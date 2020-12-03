import {useMutation} from '@apollo/client';
import {Colors, NonIdealState, Switch, Tooltip} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {TickTag} from 'src/JobTick';
import {timestampToString, TimezoneContext} from 'src/TimeComponents';
import {
  displayScheduleMutationErrors,
  START_SCHEDULE_MUTATION,
  STOP_SCHEDULE_MUTATION,
} from 'src/schedules/ScheduleRow';
import {humanCronString} from 'src/schedules/humanCronString';
import {ScheduleFragment} from 'src/schedules/types/ScheduleFragment';
import {StartSchedule} from 'src/schedules/types/StartSchedule';
import {StopSchedule} from 'src/schedules/types/StopSchedule';
import {JobStatus, JobType} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {ButtonLink} from 'src/ui/ButtonLink';
import {CountdownStatus, useCountdown} from 'src/ui/Countdown';
import {Group} from 'src/ui/Group';
import {MetadataTable} from 'src/ui/MetadataTable';
import {RefreshableCountdown} from 'src/ui/RefreshableCountdown';
import {Code, Heading} from 'src/ui/Text';
import {FontFamily} from 'src/ui/styles';
import {useScheduleSelector} from 'src/workspace/WorkspaceContext';
import {repoAddressAsString} from 'src/workspace/repoAddressAsString';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

interface TimestampDisplayProps {
  timestamp: number;
  timezone: string | null;
}

const TimestampDisplay = (props: TimestampDisplayProps) => {
  const {timestamp, timezone} = props;
  const [userTimezone] = React.useContext(TimezoneContext);

  return (
    <span>
      {timestampToString({unix: timestamp, format: 'MMM DD, h:mm A z'}, timezone || userTimezone)}
    </span>
  );
};

export const ScheduleDetails: React.FC<{
  schedule: ScheduleFragment;
  repoAddress: RepoAddress;
  countdownDuration: number;
  countdownStatus: CountdownStatus;
  onRefresh: () => void;
}> = (props) => {
  const {repoAddress, schedule, countdownDuration, countdownStatus, onRefresh} = props;
  const {cronSchedule, executionTimezone, futureTicks, name, partitionSet, pipelineName} = schedule;

  const [copyText, setCopyText] = React.useState('Click to copy');

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

  const scheduleSelector = useScheduleSelector(name);

  const timeRemaining = useCountdown({
    duration: countdownDuration,
    status: countdownStatus,
  });

  // Restore the tooltip text after a delay.
  React.useEffect(() => {
    let token: any;
    if (copyText === 'Copied!') {
      token = setTimeout(() => {
        setCopyText('Click to copy');
      }, 2000);
    }
    return () => {
      token && clearTimeout(token);
    };
  }, [copyText]);

  const {scheduleState} = schedule;

  // TODO dish: Port over something like the existing UI
  if (!scheduleState) {
    return (
      <NonIdealState
        icon="time"
        title="Schedule not found"
        description={
          <>
            Schedule <strong>{name}</strong> not found in{' '}
            <strong>{repoAddressAsString(repoAddress)}</strong>
          </>
        }
      />
    );
  }

  const {status, id, ticks} = scheduleState;
  const latestTick = ticks.length > 0 ? ticks[0] : null;

  const onChangeSwitch = () => {
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

  const copyId = () => {
    navigator.clipboard.writeText(id);
    setCopyText('Copied!');
  };

  const running = status === JobStatus.RUNNING;
  const countdownRefreshing = countdownStatus === 'idle' || timeRemaining === 0;
  const seconds = Math.floor(timeRemaining / 1000);

  return (
    <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-start'}}>
      <Group direction="vertical" spacing={12}>
        <Group alignItems="center" direction="horizontal" spacing={4}>
          <Heading>{name}</Heading>
          <Box margin={{left: 12}}>
            <Switch
              checked={running}
              inline
              large
              disabled={toggleOffInFlight || toggleOnInFlight}
              innerLabelChecked="on"
              innerLabel="off"
              onChange={onChangeSwitch}
              style={{margin: '2px 0 0 0'}}
            />
          </Box>
          {futureTicks.results.length && running ? (
            <Group direction="horizontal" spacing={4}>
              <div>Next tick:</div>
              <TimestampDisplay
                timestamp={futureTicks.results[0].timestamp}
                timezone={executionTimezone}
              />
            </Group>
          ) : null}
        </Group>
        <MetadataTable
          rows={[
            {
              key: 'Latest tick',
              value: latestTick ? (
                <Group direction="horizontal" spacing={8} alignItems="center">
                  <TimestampDisplay timestamp={latestTick.timestamp} timezone={executionTimezone} />
                  <TickTag tick={latestTick} jobType={JobType.SCHEDULE} />
                </Group>
              ) : (
                'Schedule has never run'
              ),
            },
            {
              key: 'Pipeline',
              value: (
                <Link to={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}/`)}>
                  {pipelineName}
                </Link>
              ),
            },
            {
              key: 'Schedule',
              value: cronSchedule ? (
                <Group direction="horizontal" spacing={8}>
                  <span>{humanCronString(cronSchedule)}</span>
                  <Code>({cronSchedule})</Code>
                </Group>
              ) : (
                <div>-</div>
              ),
            },
            {
              key: 'Mode',
              value: schedule.mode,
            },
            {
              key: 'Partition set',
              value: partitionSet ? (
                <Link
                  to={workspacePathFromAddress(
                    repoAddress,
                    `/pipelines/${pipelineName}/partitions`,
                  )}
                >
                  {partitionSet.name}
                </Link>
              ) : (
                'None'
              ),
            },
          ]}
        />
      </Group>
      <Box margin={{top: 4}}>
        <Group direction="vertical" spacing={8} alignItems="flex-end">
          <RefreshableCountdown
            refreshing={countdownRefreshing}
            seconds={seconds}
            onRefresh={onRefresh}
          />
          <Tooltip content={copyText}>
            <ButtonLink color={{link: Colors.GRAY3, hover: Colors.GRAY1}} onClick={copyId}>
              <span style={{fontFamily: FontFamily.monospace}}>{`id: ${id.slice(0, 8)}`}</span>
            </ButtonLink>
          </Tooltip>
        </Group>
      </Box>
    </Box>
  );
};
