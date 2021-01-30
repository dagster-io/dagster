import {useMutation} from '@apollo/client';
import {Switch} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {TickTag} from 'src/jobs/JobTick';
import {TimestampDisplay} from 'src/schedules/TimestampDisplay';
import {
  displaySensorMutationErrors,
  START_SENSOR_MUTATION,
  STOP_SENSOR_MUTATION,
} from 'src/sensors/SensorMutations';
import {SensorFragment} from 'src/sensors/types/SensorFragment';
import {StartSensor} from 'src/sensors/types/StartSensor';
import {StopSensor} from 'src/sensors/types/StopSensor';
import {JobStatus, JobType} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {CountdownStatus, useCountdown} from 'src/ui/Countdown';
import {Group} from 'src/ui/Group';
import {MetadataTable} from 'src/ui/MetadataTable';
import {RefreshableCountdown} from 'src/ui/RefreshableCountdown';
import {Heading} from 'src/ui/Text';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

export const humanizeSensorInterval = (minIntervalSeconds?: number) => {
  if (!minIntervalSeconds) {
    minIntervalSeconds = 30; // should query sensor interval config when available
  }
  minIntervalSeconds = Math.max(30, minIntervalSeconds);
  if (minIntervalSeconds < 60 || minIntervalSeconds % 60) {
    return `~ ${minIntervalSeconds} sec`;
  }
  if (minIntervalSeconds === 3600) {
    return `~ 1 hour`;
  }
  if (minIntervalSeconds < 3600 || minIntervalSeconds % 3600) {
    return `~ ${minIntervalSeconds / 60} min`;
  }
  if (minIntervalSeconds === 86400) {
    return `~ 1 day`;
  }
  if (minIntervalSeconds < 86400 || minIntervalSeconds % 86400) {
    return `~ ${minIntervalSeconds / 3600} hours`;
  }
  return `~ ${minIntervalSeconds / 86400} days`;
};

export const SensorDetails: React.FC<{
  sensor: SensorFragment;
  repoAddress: RepoAddress;
  daemonHealth: boolean | null;
  countdownDuration: number;
  countdownStatus: CountdownStatus;
  onRefresh: () => void;
}> = ({sensor, repoAddress, daemonHealth, countdownDuration, countdownStatus, onRefresh}) => {
  const {
    name,
    pipelineName,
    jobOriginId,
    sensorState: {status, ticks},
  } = sensor;

  const sensorSelector = {
    ...repoAddressToSelector(repoAddress),
    sensorName: name,
  };
  const [startSensor, {loading: toggleOnInFlight}] = useMutation<StartSensor>(
    START_SENSOR_MUTATION,
    {onCompleted: displaySensorMutationErrors},
  );
  const [stopSensor, {loading: toggleOffInFlight}] = useMutation<StopSensor>(STOP_SENSOR_MUTATION, {
    onCompleted: displaySensorMutationErrors,
  });
  const timeRemaining = useCountdown({
    duration: countdownDuration,
    status: countdownStatus,
  });

  const countdownRefreshing = countdownStatus === 'idle' || timeRemaining === 0;
  const seconds = Math.floor(timeRemaining / 1000);

  const onChangeSwitch = () => {
    if (status === JobStatus.RUNNING) {
      stopSensor({variables: {jobOriginId}});
    } else {
      startSensor({variables: {sensorSelector}});
    }
  };

  const latestTick = ticks.length ? ticks[0] : null;

  return (
    <Box flex={{direction: 'row', justifyContent: 'space-between', alignItems: 'flex-start'}}>
      <Group direction="column" spacing={12}>
        <Group alignItems="center" direction="row" spacing={8}>
          <Heading>{name}</Heading>
          <Box margin={{left: 4}}>
            <Switch
              checked={status === JobStatus.RUNNING}
              inline
              large
              disabled={toggleOffInFlight || toggleOnInFlight}
              innerLabelChecked="on"
              innerLabel="off"
              onChange={onChangeSwitch}
              style={{margin: '4px 0 0 0'}}
            />
          </Box>
          {sensor.nextTick && daemonHealth && status === JobStatus.RUNNING ? (
            <Group direction="row" spacing={4}>
              <div>Next tick:</div>
              <TimestampDisplay timestamp={sensor.nextTick.timestamp} />
            </Group>
          ) : null}
        </Group>
        <MetadataTable
          rows={[
            {
              key: 'Latest tick',
              value: latestTick ? (
                <Group direction="row" spacing={8} alignItems="center">
                  <TimestampDisplay timestamp={latestTick.timestamp} />
                  <TickTag tick={latestTick} jobType={JobType.SENSOR} />
                </Group>
              ) : (
                'Sensor has never run'
              ),
            },
            {
              key: 'Pipeline',
              value: (
                <Link to={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}`)}>
                  {pipelineName}
                </Link>
              ),
            },
            {
              key: 'Mode',
              value: sensor.mode,
            },
            {
              key: 'Frequency',
              value: humanizeSensorInterval(sensor.minIntervalSeconds),
            },
          ]}
        />
      </Group>
      <Box margin={{top: 4}}>
        <RefreshableCountdown
          refreshing={countdownRefreshing}
          seconds={seconds}
          onRefresh={onRefresh}
        />
      </Box>
    </Box>
  );
};
