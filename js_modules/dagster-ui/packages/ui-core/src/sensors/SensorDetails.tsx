import {QueryResult} from '@apollo/client';
import {
  Box,
  Button,
  FontFamily,
  Heading,
  Icon,
  MetadataTableWIP,
  PageHeader,
  Tag,
} from '@dagster-io/ui-components';
import {useState} from 'react';

import {EditCursorDialog} from './EditCursorDialog';
import {SensorMonitoredAssets} from './SensorMonitoredAssets';
import {SensorResetButton} from './SensorResetButton';
import {SensorSwitch} from './SensorSwitch';
import {SensorTargetList} from './SensorTargetList';
import {SensorFragment} from './types/SensorFragment.types';
import {
  SensorAssetSelectionQuery,
  SensorAssetSelectionQueryVariables,
} from './types/SensorRoot.types';
import {QueryRefreshCountdown, QueryRefreshState} from '../app/QueryRefresh';
import {InstigationStatus, SensorType} from '../graphql/types';
import {RepositoryLink} from '../nav/RepositoryLink';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {SensorDryRunDialog} from '../ticks/SensorDryRunDialog';
import {TickStatusTag} from '../ticks/TickStatusTag';
import {RepoAddress} from '../workspace/types';

const TIME_FORMAT = {showSeconds: true, showTimezone: false};

export const humanizeSensorInterval = (minIntervalSeconds?: number) => {
  if (!minIntervalSeconds) {
    minIntervalSeconds = 30; // should query sensor interval config when available
  }
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
  selectionQueryResult,
}: {
  sensor: SensorFragment;
  repoAddress: RepoAddress;
  daemonHealth: boolean | null;
  refreshState: QueryRefreshState;
  selectionQueryResult: QueryResult<SensorAssetSelectionQuery, SensorAssetSelectionQueryVariables>;
}) => {
  const {
    name,
    sensorState: {status, ticks},
    metadata,
  } = sensor;

  const [isCursorEditing, setCursorEditing] = useState(false);
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

  const [showTestTickDialog, setShowTestTickDialog] = useState(false);
  const running = status === InstigationStatus.RUNNING;

  const assetSelectionResult = selectionQueryResult.data?.sensorOrError;

  const assetSelectionData =
    assetSelectionResult?.__typename === 'Sensor' ? assetSelectionResult : null;
  const selectedAssets = assetSelectionData?.assetSelection;

  return (
    <>
      <PageHeader
        title={<Heading>{name}</Heading>}
        icon="sensors"
        tags={
          <Tag icon="sensors">
            Sensor in <RepositoryLink repoAddress={repoAddress} />
          </Tag>
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
                    <TimestampDisplay timestamp={latestTick.timestamp} timeFormat={TIME_FORMAT} />
                    <TickStatusTag tick={latestTick} />
                  </Box>
                </>
              ) : (
                'Sensor has never run'
              )}
            </td>
          </tr>
          {sensor.nextTick && daemonHealth && running && (
            <tr>
              <td>Next tick</td>
              <td>
                <TimestampDisplay timestamp={sensor.nextTick.timestamp!} timeFormat={TIME_FORMAT} />
              </td>
            </tr>
          )}
          {(sensor.targets && sensor.targets.length) || selectedAssets ? (
            <tr>
              <td>Target</td>
              <td>
                <SensorTargetList
                  targets={sensor.targets}
                  repoAddress={repoAddress}
                  selectionQueryResult={selectionQueryResult}
                  sensorType={sensor.sensorType}
                />
              </td>
            </tr>
          ) : null}
          <tr>
            <td>
              <Box flex={{alignItems: 'center'}} style={{height: '32px'}}>
                Running
              </Box>
            </td>
            <td>
              <Box
                flex={{direction: 'row', gap: 12, alignItems: 'center'}}
                style={{height: '32px'}}
              >
                <SensorSwitch repoAddress={repoAddress} sensor={sensor} />
                {sensor.canReset && <SensorResetButton repoAddress={repoAddress} sensor={sensor} />}
              </Box>
            </td>
          </tr>
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
          {sensor.sensorType !== SensorType.AUTO_MATERIALIZE ? (
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
