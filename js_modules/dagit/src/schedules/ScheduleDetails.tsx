import {useMutation} from '@apollo/client';
import {NonIdealState, Switch} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {timestampToString, TimezoneContext} from 'src/TimeComponents';
import {
  displayScheduleMutationErrors,
  START_SCHEDULE_MUTATION,
  STOP_SCHEDULE_MUTATION,
  TickTag,
} from 'src/schedules/ScheduleRow';
import {humanCronString} from 'src/schedules/humanCronString';
import {ScheduleDefinitionFragment} from 'src/schedules/types/ScheduleDefinitionFragment';
import {ScheduleStatus} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {MetadataTable} from 'src/ui/MetadataTable';
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
  schedule: ScheduleDefinitionFragment;
  repoAddress: RepoAddress;
}> = (props) => {
  const {repoAddress, schedule} = props;
  const {cronSchedule, executionTimezone, futureTicks, name, partitionSet, pipelineName} = schedule;

  const [startSchedule, {loading: toggleOnInFlight}] = useMutation(START_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
  });
  const [stopSchedule, {loading: toggleOffInFlight}] = useMutation(STOP_SCHEDULE_MUTATION, {
    onCompleted: displayScheduleMutationErrors,
  });

  const scheduleSelector = useScheduleSelector(name);

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

  const {status, ticks, scheduleOriginId} = scheduleState;
  const latestTick = ticks.length > 0 ? ticks[0] : null;

  const onChangeSwitch = () => {
    if (status === ScheduleStatus.RUNNING) {
      stopSchedule({
        variables: {scheduleOriginId},
      });
    } else {
      startSchedule({
        variables: {scheduleSelector},
      });
    }
  };

  return (
    <Group direction="vertical" spacing={12}>
      <Group alignItems="center" direction="horizontal" spacing={8}>
        <Heading>{name}</Heading>
        <Box margin={{left: 4}}>
          <Switch
            checked={status === ScheduleStatus.RUNNING}
            inline
            large
            disabled={toggleOffInFlight || toggleOnInFlight}
            innerLabelChecked="on"
            innerLabel="off"
            onChange={onChangeSwitch}
            style={{margin: '4px 0 0 0'}}
          />
        </Box>
      </Group>
      <MetadataTable
        rows={[
          {
            key: 'Schedule ID',
            value: <div style={{fontFamily: FontFamily.monospace}}>{scheduleOriginId}</div>,
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
                to={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}/partitions`)}
              >
                {partitionSet.name}
              </Link>
            ) : (
              'None'
            ),
          },
          {
            key: 'Latest tick',
            value: latestTick ? (
              <Group direction="horizontal" spacing={8} alignItems="center">
                <TimestampDisplay timestamp={latestTick.timestamp} timezone={executionTimezone} />
                <TickTag
                  status={latestTick.status}
                  eventSpecificData={latestTick.tickSpecificData}
                />
              </Group>
            ) : (
              'None'
            ),
          },
          {
            key: 'Next tick',
            value: futureTicks.results.length ? (
              <TimestampDisplay
                timestamp={futureTicks.results[0].timestamp}
                timezone={executionTimezone}
              />
            ) : (
              'None'
            ),
          },
        ]}
      />
    </Group>
  );
};
