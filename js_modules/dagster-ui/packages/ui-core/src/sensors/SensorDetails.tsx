import {
  Box,
  Button,
  FontFamily,
  Icon,
  MetadataTableWIP,
  PageHeader,
  Subtitle1,
  Tag,
  Tooltip,
} from '@dagster-io/ui-components';
import {useState} from 'react';
import {Link} from 'react-router-dom';
import {SensorAlertDetails} from 'shared/sensors/SensorAlertDetails.oss';
import styled from 'styled-components';

import {EditCursorDialog} from './EditCursorDialog';
import {SensorMonitoredAssets} from './SensorMonitoredAssets';
import {SensorResetButton} from './SensorResetButton';
import {SensorSwitch} from './SensorSwitch';
import {DEFAULT_DISABLED_REASON} from '../app/Permissions';
import {QueryRefreshCountdown, QueryRefreshState} from '../app/QueryRefresh';
import {AutomationTargetList} from '../automation/AutomationTargetList';
import {AutomationAssetSelectionFragment} from '../automation/types/AutomationAssetSelectionFragment.types';
import {InstigationStatus, SensorType} from '../graphql/types';
import {RepositoryLink} from '../nav/RepositoryLink';
import {DefinitionOwners} from '../owners/DefinitionOwners';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {EvaluateTickButtonSensor} from '../ticks/EvaluateTickButtonSensor';
import {SensorFragment} from './types/SensorFragment.types';
import {TickStatusTag} from '../ticks/TickStatusTag';
import {RepoAddress} from '../workspace/types';

const TIME_FORMAT = {showSeconds: true, showTimezone: false};

/** Some cursors are persisted Python tuples, which come through as JSON. Examples:
 * {"__class__": "AirflowPollingSensorCursor", "dag_query_offset": 0, "end_date_gte": 1743134332.087687, "end_date_lte": null}
 * {"__class__": "RunStatusSensorCursor", "record_id": 1234, "update_timestamp": "1743134332.087687", "record_timestamp": null}
 *
 * For these, there are often empty / unused fields and we can pull just the cursor fields that are in use
 * into a compact table-ready presentation:
 *
 * end_date_gte=1743134332.087687
 */
export const humanizeSensorCursor = (cursor: string | false | null) => {
  if (cursor && cursor.startsWith('{"__class__"')) {
    const cursorObj = JSON.parse(cursor);
    delete cursorObj['__class__'];
    return Object.entries(cursorObj)
      .filter((pair) => pair[1] !== null && pair[1] !== 0)
      .map(([k, v]) => `${k}=${v}`)
      .join(',');
  }
  return cursor;
};

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

  const running = status === InstigationStatus.RUNNING;

  return (
    <>
      <PageHeader
        title={
          <Subtitle1 style={{display: 'flex', flexDirection: 'row', gap: 4}}>
            <Link to="/automation">自动化</Link>
            <span>/</span>
            {name}
          </Subtitle1>
        }
        icon="sensors"
        tags={
          <Tag icon="sensors">
            监控器位于 <RepositoryLink repoAddress={repoAddress} />
          </Tag>
        }
        right={
          <Box margin={{top: 4}} flex={{direction: 'row', alignItems: 'center', gap: 8}}>
            <QueryRefreshCountdown refreshState={refreshState} />
            <EvaluateTickButtonSensor
              cursor={cursor || ''}
              name={sensor.name}
              repoAddress={repoAddress}
              jobName={sensor.targets?.[0]?.pipelineName || ''}
              sensorType={sensor.sensorType}
            />
          </Box>
        }
      />
      <MetadataTableWIP>
        <tbody>
          {sensor.description ? (
            <tr>
              <td>描述</td>
              <td>{sensor.description}</td>
            </tr>
          ) : null}
          {sensor.owners.length > 0 && (
            <tr>
              <td>负责人</td>
              <td>
                <DefinitionOwners owners={sensor.owners} />
              </td>
            </tr>
          )}
          <tr>
            <td>最近触发</td>
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
                '监控器从未运行'
              )}
            </td>
          </tr>
          {sensor.nextTick && daemonHealth && running && (
            <tr>
              <td>下次触发</td>
              <td>
                {/* eslint-disable-next-line @typescript-eslint/no-non-null-assertion */}
                <TimestampDisplay timestamp={sensor.nextTick.timestamp!} timeFormat={TIME_FORMAT} />
              </td>
            </tr>
          )}
          {(sensor.targets && sensor.targets.length) || assetSelection ? (
            <tr>
              <td>目标</td>
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
                运行状态
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
            <td>频率</td>
            <td>{humanizeSensorInterval(sensor.minIntervalSeconds)}</td>
          </tr>
          {metadata.assetKeys && metadata.assetKeys.length ? (
            <tr>
              <td>监控的资产</td>
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
                  游标
                </Box>
              </td>
              <td>
                <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
                  <span style={{fontFamily: FontFamily.monospace, fontSize: '14px'}}>
                    {cursor ? humanizeSensorCursor(cursor) : '无'}
                  </span>
                  <Tooltip
                    canShow={!sensor.hasCursorUpdatePermissions}
                    content={DEFAULT_DISABLED_REASON}
                  >
                    <Button
                      icon={<Icon name="edit" />}
                      disabled={!sensor.hasCursorUpdatePermissions}
                      onClick={() => setCursorEditing(true)}
                    >
                      {cursor !== humanizeSensorCursor(cursor) ? '查看原始 / 编辑' : '编辑'}
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
          <SensorAlertDetails repoAddress={repoAddress} sensorName={name} />
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
