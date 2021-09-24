import * as React from 'react';
import {Link} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {TickTag} from '../instigation/InstigationTick';
import {RepositoryLink} from '../nav/RepositoryLink';
import {PipelineReference} from '../pipelines/PipelineReference';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {InstigationStatus, InstigationType} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {CountdownStatus, useCountdown} from '../ui/Countdown';
import {Group} from '../ui/Group';
import {MetadataTable} from '../ui/MetadataTable';
import {PageHeader} from '../ui/PageHeader';
import {RefreshableCountdown} from '../ui/RefreshableCountdown';
import {Heading} from '../ui/Text';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {SensorSwitch} from './SensorSwitch';
import {SensorFragment} from './types/SensorFragment';

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
    sensorState: {status, ticks},
  } = sensor;
  const {flagPipelineModeTuples} = useFeatureFlags();

  const timeRemaining = useCountdown({
    duration: countdownDuration,
    status: countdownStatus,
  });

  const countdownRefreshing = countdownStatus === 'idle' || timeRemaining === 0;
  const seconds = Math.floor(timeRemaining / 1000);

  const latestTick = ticks.length ? ticks[0] : null;
  const hasMultipleTargets = sensor.targets && sensor.targets.length > 1;

  return (
    <Group direction="column" spacing={16}>
      <PageHeader
        title={
          <Group alignItems="center" direction="row" spacing={2}>
            <Heading>{name}</Heading>
            <Box margin={{horizontal: 12}}>
              <SensorSwitch repoAddress={repoAddress} sensor={sensor} />
            </Box>
            {sensor.nextTick && daemonHealth && status === InstigationStatus.RUNNING ? (
              <Group direction="row" spacing={4}>
                <div>Next tick:</div>
                <TimestampDisplay timestamp={sensor.nextTick.timestamp} />
              </Group>
            ) : null}
          </Group>
        }
        icon="sensors"
        description={
          <>
            <Link to={workspacePathFromAddress(repoAddress, '/sensors')}>Sensor</Link> in{' '}
            <RepositoryLink repoAddress={repoAddress} />
          </>
        }
        right={
          <Box margin={{top: 4}}>
            <RefreshableCountdown
              refreshing={countdownRefreshing}
              seconds={seconds}
              onRefresh={onRefresh}
            />
          </Box>
        }
      />
      <MetadataTable
        rows={[
          sensor.description
            ? {
                key: 'Description',
                value: sensor.description,
              }
            : null,
          {
            key: 'Latest tick',
            value: latestTick ? (
              <Group direction="row" spacing={8} alignItems="center">
                <TimestampDisplay timestamp={latestTick.timestamp} />
                <TickTag tick={latestTick} instigationType={InstigationType.SENSOR} />
              </Group>
            ) : (
              'Sensor has never run'
            ),
          },
          {
            key: flagPipelineModeTuples
              ? hasMultipleTargets
                ? 'Jobs'
                : 'Job'
              : hasMultipleTargets
              ? 'Pipelines'
              : 'Pipeline',
            value:
              sensor.targets && sensor.targets.length ? (
                <Group direction="column" spacing={2}>
                  {sensor.targets.map((target) =>
                    target.pipelineName ? (
                      <PipelineReference
                        key={`${target.pipelineName}:${target.mode}`}
                        pipelineName={target.pipelineName}
                        pipelineHrefContext={repoAddress}
                        mode={target.mode}
                      />
                    ) : null,
                  )}
                </Group>
              ) : (
                'Sensor does not target a pipeline'
              ),
          },
          {
            key: 'Frequency',
            value: humanizeSensorInterval(sensor.minIntervalSeconds),
          },
        ]}
      />
    </Group>
  );
};
