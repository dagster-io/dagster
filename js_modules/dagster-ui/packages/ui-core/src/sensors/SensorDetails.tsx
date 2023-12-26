import {
  Box,
  Button,
  MetadataTableWIP,
  PageHeader,
  Tag,
  Heading,
  FontFamily,
  Icon,
} from '@dagster-io/ui-components';
import * as React from 'react';

import {QueryRefreshCountdown, QueryRefreshState} from '../app/QueryRefresh';
import {InstigationStatus, SensorType} from '../graphql/types';
import {RepositoryLink} from '../nav/RepositoryLink';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {SensorDryRunDialog} from '../ticks/SensorDryRunDialog';
import {TickStatusTag} from '../ticks/TickStatusTag';
import {RepoAddress} from '../workspace/types';

import {EditCursorDialog} from './EditCursorDialog';
import {SensorMonitoredAssets} from './SensorMonitoredAssets';
import {SensorSwitch} from './SensorSwitch';
import {SensorTargetList} from './SensorTargetList';
import {SensorFragment} from './types/SensorFragment.types';

export const humanizeSensorInterval = (minIntervalSeconds?: number) => {
  if (!minIntervalSeconds) {
    minIntervalSeconds = 30; // should query sensor interval config when available
  }
  minIntervalSeconds = Math.max(30, minIntervalSeconds);
  if (minIntervalSeconds < 60 || minIntervalSeconds % 60) {
    return `~${minIntervalSeconds} sec`;
  }
  if (minIntervalSeconds === 3600) {
    return `~1 hour`;
  }
  if (minIntervalSeconds < 3600 || minIntervalSeconds % 3600) {
    return `~${minIntervalSeconds / 60} min`;
  }
  if (minIntervalSeconds === 86400) {
    return `~1 day`;
  }
  if (minIntervalSeconds < 86400 || minIntervalSeconds % 86400) {
    return `~${minIntervalSeconds / 3600} hours`;
  }
  return `~${minIntervalSeconds / 86400} days`;
};

export const SensorDetails = ({
  sensor,
  repoAddress,
  daemonHealth,
  refreshState,
}: {
  sensor: SensorFragment;
  repoAddress: RepoAddress;
  daemonHealth: boolean | null;
  refreshState: QueryRefreshState;
}) => {
  const {
    name,
    sensorState: {status, ticks},
    metadata,
  } = sensor;

  const [isCursorEditing, setCursorEditing] = React.useState(false);
  const sensorSelector = {
    sensorName: sensor.name,
    repositoryName: repoAddress.name,
    repositoryLocationName: repoAddress.location,
  };

  const latestTick = ticks.length ? ticks[0] : null;
  const cursor =
    sensor.sensorState.typeSpecificData &&
    sensor.sensorState.typeSpecificData.__typename === 'SensorData' &&
    sensor.sensorState.typeSpecificData.lastCursor;

  const [showTestTickDialog, setShowTestTickDialog] = React.useState(false);
  const running = status === InstigationStatus.RUNNING;

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
            {sensor.nextTick && daemonHealth && running ? (
              <Tag icon="timer">
                Next tick: <TimestampDisplay timestamp={sensor.nextTick.timestamp!} />
              </Tag>
            ) : null}
          </>
        }
        right={
          <Box margin={{top: 4}} flex={{direction: 'row', alignItems: 'center', gap: 8}}>
            <QueryRefreshCountdown refreshState={refreshState} />
            {sensor.sensorType === SensorType.STANDARD ? (
              <Button
                onClick={() => {
                  setShowTestTickDialog(true);
                }}
              >
                Test Sensor
              </Button>
            ) : null}
          </Box>
        }
      />
      <SensorDryRunDialog
        isOpen={showTestTickDialog}
        onClose={() => {
          setShowTestTickDialog(false);
        }}
        currentCursor={cursor || ''}
        name={sensor.name}
        repoAddress={repoAddress}
        jobName={sensor.targets?.[0]?.pipelineName || ''}
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
                    <TickStatusTag tick={latestTick} />
                  </Box>
                </>
              ) : (
                'Sensor has never run'
              )}
            </td>
          </tr>
          {sensor.targets && sensor.targets.length ? (
            <tr>
              <td>Target</td>
              <td>
                <SensorTargetList targets={sensor.targets} repoAddress={repoAddress} />
              </td>
            </tr>
          ) : null}
          <tr>
            <td>Frequency</td>
            <td>{humanizeSensorInterval(sensor.minIntervalSeconds)}</td>
          </tr>
          {metadata.assetKeys && metadata.assetKeys.length ? (
            <tr>
              <td>Monitored assets</td>
              <td>
                <SensorMonitoredAssets metadata={metadata} />
              </td>
            </tr>
          ) : null}
          {sensor.sensorType !== SensorType.AUTOMATION_POLICY ? (
            <tr>
              <td>
                <Box flex={{alignItems: 'center'}} style={{height: '32px'}}>
                  Cursor
                </Box>
              </td>
              <td>
                <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
                  <span style={{fontFamily: FontFamily.monospace, fontSize: '16px'}}>
                    {cursor ? cursor : 'None'}
                  </span>
                  <Button icon={<Icon name="edit" />} onClick={() => setCursorEditing(true)}>
                    Edit
                  </Button>
                </Box>
                <EditCursorDialog
                  isOpen={isCursorEditing}
                  sensorSelector={sensorSelector}
                  cursor={cursor ? cursor : ''}
                  onClose={() => setCursorEditing(false)}
                />
              </td>
            </tr>
          ) : null}
        </tbody>
      </MetadataTableWIP>
    </>
  );
};
