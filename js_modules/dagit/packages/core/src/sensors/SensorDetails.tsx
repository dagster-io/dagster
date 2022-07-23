import {
  Box,
  Button,
  Group,
  MetadataTableWIP,
  PageHeader,
  Tag,
  Heading,
  FontFamily,
} from '@dagster-io/ui';
import * as React from 'react';

import {QueryRefreshCountdown, QueryRefreshState} from '../app/QueryRefresh';
import {AssetLink} from '../assets/AssetLink';
import {TickTag} from '../instigation/InstigationTick';
import {RepositoryLink} from '../nav/RepositoryLink';
import {PipelineReference} from '../pipelines/PipelineReference';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {InstigationStatus, InstigationType} from '../types/globalTypes';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';

import {EditCursorDialog} from './EditCursorDialog';
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
  refreshState: QueryRefreshState;
}> = ({sensor, repoAddress, daemonHealth, refreshState}) => {
  const {
    name,
    sensorState: {status, ticks},
    targets,
    metadata,
  } = sensor;

  const [isCursorEditing, setCursorEditing] = React.useState(false);
  const sensorSelector = {
    sensorName: sensor.name,
    repositoryName: repoAddress.name,
    repositoryLocationName: repoAddress.location,
  };
  const repo = useRepository(repoAddress);
  const pipelinesAndJobs = repo?.repository.pipelines;

  const latestTick = ticks.length ? ticks[0] : null;
  const targetCount = targets?.length || 0;

  const targetNames = React.useMemo(
    () => new Set((targets || []).map((target) => target.pipelineName)),
    [targets],
  );

  const anyPipelines = React.useMemo(() => {
    return (pipelinesAndJobs || []).some(
      (pipelineOrJob) => !pipelineOrJob.isJob && targetNames.has(pipelineOrJob.name),
    );
  }, [pipelinesAndJobs, targetNames]);

  const pipelineOrJobLabel = React.useMemo(() => {
    if (anyPipelines) {
      return targetCount > 1 ? 'Jobs / Pipelines' : 'Pipeline';
    }
    return targetCount > 1 ? 'Jobs' : 'Job';
  }, [anyPipelines, targetCount]);

  const cursor =
    sensor.sensorState.typeSpecificData &&
    sensor.sensorState.typeSpecificData.__typename === 'SensorData' &&
    sensor.sensorState.typeSpecificData.lastCursor;

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
            <Tag icon="sensors">
              Sensor in <RepositoryLink repoAddress={repoAddress} />
            </Tag>
            {sensor.nextTick && daemonHealth && status === InstigationStatus.RUNNING ? (
              <Tag icon="timer">
                Next tick: <TimestampDisplay timestamp={sensor.nextTick.timestamp} />
              </Tag>
            ) : null}
          </>
        }
        right={
          <Box margin={{top: 4}}>
            <QueryRefreshCountdown refreshState={refreshState} />
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
                <>
                  <Box
                    flex={{direction: 'row', gap: 8, alignItems: 'center'}}
                    style={{marginTop: '-2px'}}
                  >
                    <TimestampDisplay timestamp={latestTick.timestamp} />
                    <TickTag tick={latestTick} instigationType={InstigationType.SENSOR} />
                  </Box>
                </>
              ) : (
                'Sensor has never run'
              )}
            </td>
          </tr>
          {sensor.targets && sensor.targets.length ? (
            <tr>
              <td>{pipelineOrJobLabel}</td>
              <td>
                <Group direction="column" spacing={2}>
                  {sensor.targets.map((target) =>
                    target.pipelineName ? (
                      <PipelineReference
                        key={target.pipelineName}
                        pipelineName={target.pipelineName}
                        pipelineHrefContext={repoAddress}
                        isJob={!!(repo && isThisThingAJob(repo, target.pipelineName))}
                      />
                    ) : null,
                  )}
                </Group>
              </td>
            </tr>
          ) : null}
          <tr>
            <td>Cursor</td>
            <td>
              {isCursorEditing ? (
                <EditCursorDialog
                  sensorSelector={sensorSelector}
                  cursor={cursor ? cursor : ''}
                  onClose={() => setCursorEditing(false)}
                />
              ) : null}
              <Box flex={{direction: 'row', alignItems: 'center'}}>
                <Box style={{fontFamily: FontFamily.monospace, marginRight: 10}}>
                  {cursor ? cursor : 'None'}
                </Box>
                <Button onClick={() => setCursorEditing(true)}>Edit</Button>
              </Box>
            </td>
          </tr>
          <tr>
            <td>Frequency</td>
            <td>{humanizeSensorInterval(sensor.minIntervalSeconds)}</td>
          </tr>
          {metadata.assetKeys && metadata.assetKeys.length ? (
            <tr>
              <td>Monitored Assets</td>
              <td>
                <Box flex={{direction: 'column', gap: 2}}>
                  {metadata.assetKeys.map((key) => (
                    <AssetLink key={key.path.join('/')} path={key.path} icon="asset" />
                  ))}
                </Box>
              </td>
            </tr>
          ) : null}
        </tbody>
      </MetadataTableWIP>
    </>
  );
};
