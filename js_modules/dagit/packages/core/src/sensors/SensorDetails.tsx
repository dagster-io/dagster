import * as React from 'react';

import {useFeatureFlags} from '../app/Flags';
import {TickTag} from '../instigation/InstigationTick';
import {RepositoryLink} from '../nav/RepositoryLink';
import {PipelineReference} from '../pipelines/PipelineReference';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {InstigationStatus, InstigationType} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {CountdownStatus, useCountdown} from '../ui/Countdown';
import {Group} from '../ui/Group';
import {MetadataTableWIP} from '../ui/MetadataTable';
import {PageHeader} from '../ui/PageHeader';
import {RefreshableCountdown} from '../ui/RefreshableCountdown';
import {TagWIP} from '../ui/TagWIP';
import {Heading} from '../ui/Text';
import {RepoAddress} from '../workspace/types';

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
    <>
      <PageHeader
        title={
          <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
            <Heading>{name}</Heading>
            <SensorSwitch repoAddress={repoAddress} sensor={sensor} />
          </Box>
        }
        icon="sensors"
        tags={
          <>
            <TagWIP icon="sensors">
              Sensor in <RepositoryLink repoAddress={repoAddress} />
            </TagWIP>
            {sensor.nextTick && daemonHealth && status === InstigationStatus.RUNNING ? (
              <TagWIP icon="timer">
                Next tick: <TimestampDisplay timestamp={sensor.nextTick.timestamp} />
              </TagWIP>
            ) : null}
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
      <MetadataTableWIP>
        <tbody>
          {sensor.description ? (
            <tr>
              <td>Description</td>
              <td>{sensor.description}</td>
            </tr>
          ) : null}
          <tr>
            <td>Latest tick</td>
            <td>
              {latestTick ? (
                <Box
                  flex={{direction: 'row', gap: 8, alignItems: 'center'}}
                  style={{marginTop: '-2px'}}
                >
                  <TimestampDisplay timestamp={latestTick.timestamp} />
                  <TickTag tick={latestTick} instigationType={InstigationType.SENSOR} />
                </Box>
              ) : (
                'Sensor has never run'
              )}
            </td>
          </tr>
          <tr>
            <td>
              {flagPipelineModeTuples
                ? hasMultipleTargets
                  ? 'Jobs'
                  : 'Job'
                : hasMultipleTargets
                ? 'Pipelines'
                : 'Pipeline'}
            </td>
            <td>
              {sensor.targets && sensor.targets.length ? (
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
              )}
            </td>
          </tr>
          <tr>
            <td>Frequency</td>
            <td>{humanizeSensorInterval(sensor.minIntervalSeconds)}</td>
          </tr>
        </tbody>
      </MetadataTableWIP>
    </>
  );
};
