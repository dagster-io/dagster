import {
  Box,
  Button,
  FontFamily,
  Heading,
  Icon,
  MetadataTableWIP,
  PageHeader,
  Tag,
  Tooltip,
} from '@dagster-io/ui-components';
import {useState} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {EditCursorDialog} from './EditCursorDialog';
import {SensorMonitoredAssets} from './SensorMonitoredAssets';
import {SensorResetButton} from './SensorResetButton';
import {SensorSwitch} from './SensorSwitch';
import {SensorFragment} from './types/SensorFragment.types';
import {usePermissionsForLocation} from '../app/Permissions';
import {QueryRefreshCountdown, QueryRefreshState} from '../app/QueryRefresh';
import {AutomationTargetList} from '../automation/AutomationTargetList';
import {AutomationAssetSelectionFragment} from '../automation/types/AutomationAssetSelectionFragment.types';
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
  assetSelection,
}: {
  sensor: SensorFragment;
  repoAddress: RepoAddress;
  daemonHealth: boolean | null;
  refreshState: QueryRefreshState;
  assetSelection: AutomationAssetSelectionFragment | null;
}) => {
  const {
    name,
    sensorState: {status, ticks},
    metadata,
  } = sensor;

  const {
    permissions,
    disabledReasons,
    loading: loadingPermissions,
  } = usePermissionsForLocation(repoAddress.location);
  const {canUpdateSensorCursor} = permissions;

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

  return (
    <>
      <PageHeader
        title={
          <Heading style={{display: 'flex', flexDirection: 'row', gap: 4}}>
            <Link to="/automation">Automation</Link>
            <span>/</span>
            {name}
          </Heading>
        }
        icon="sensors"
        tags={
          <Tag icon="sensors">
            Sensor in <RepositoryLink repoAddress={repoAddress} />
          </Tag>
        }
        right={
          <Box margin={{top: 4}} flex={{direction: 'row', alignItems: 'center', gap: 8}}>
            <QueryRefreshCountdown refreshState={refreshState} />
            <Tooltip
              canShow={sensor.sensorType !== SensorType.STANDARD}
              content="Testing not available for this sensor type"
              placement="top-end"
            >
              <Button
                disabled={sensor.sensorType !== SensorType.STANDARD}
                onClick={() => {
                  setShowTestTickDialog(true);
                }}
              >
                Test sensor
              </Button>
            </Tooltip>
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
                    <TickStatusTag tick={latestTick} tickResultType="runs" />
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
          {(sensor.targets && sensor.targets.length) || assetSelection ? (
            <tr>
              <td>Target</td>
              <TargetCell>
                <AutomationTargetList
                  targets={sensor.targets}
                  repoAddress={repoAddress}
                  assetSelection={assetSelection || null}
                  automationType={sensor.sensorType}
                />
              </TargetCell>
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
          {sensor.sensorType !== SensorType.AUTO_MATERIALIZE &&
          sensor.sensorType !== SensorType.AUTOMATION ? (
            <tr>
              <td>
                <Box flex={{alignItems: 'center'}} style={{height: '32px'}}>
                  Cursor
                </Box>
              </td>
              <td>
                <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
                  <span style={{fontFamily: FontFamily.monospace, fontSize: '14px'}}>
                    {cursor ? cursor : 'None'}
                  </span>
                  <Tooltip
                    canShow={!canUpdateSensorCursor}
                    content={disabledReasons.canUpdateSensorCursor}
                  >
                    <Button
                      icon={<Icon name="edit" />}
                      disabled={!canUpdateSensorCursor || loadingPermissions}
                      onClick={() => setCursorEditing(true)}
                    >
                      Edit
                    </Button>
                  </Tooltip>
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

const TargetCell = styled.td`
  button {
    line-height: 20px;
  }
`;
