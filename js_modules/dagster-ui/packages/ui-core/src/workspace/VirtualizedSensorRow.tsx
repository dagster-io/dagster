import {
  Box,
  Caption,
  Checkbox,
  Colors,
  IconName,
  MiddleTruncate,
  Tag,
  Tooltip,
  useDelayedState,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {LoadingOrNone} from './VirtualizedWorkspaceTable';
import {RepoAddress} from './types';
import {SingleSensorQuery, SingleSensorQueryVariables} from './types/VirtualizedSensorRow.types';
import {workspacePathFromAddress} from './workspacePath';
import {gql, useQuery} from '../apollo-client';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {AutomationTargetList} from '../automation/AutomationTargetList';
import {InstigationStatus, SensorType} from '../graphql/types';
import {LastRunSummary} from '../instance/LastRunSummary';
import {TICK_TAG_FRAGMENT} from '../instigation/InstigationTick';
import {BasicInstigationStateFragment} from '../overview/types/BasicInstigationStateFragment.types';
import {RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {humanizeSensorInterval} from '../sensors/SensorDetails';
import {SENSOR_ASSET_SELECTIONS_QUERY} from '../sensors/SensorRoot';
import {SensorSwitch} from '../sensors/SensorSwitch';
import {SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitchFragment';
import {
  SensorAssetSelectionQuery,
  SensorAssetSelectionQueryVariables,
} from '../sensors/types/SensorRoot.types';
import {TickStatusTag} from '../ticks/TickStatusTag';
import {HeaderCell, HeaderRow, Row, RowCell} from '../ui/VirtualizedTable';

const TEMPLATE_COLUMNS = '1.5fr 180px 1fr 76px 120px 148px 180px';
const TEMPLATE_COLUMNS_WITH_CHECKBOX = `60px ${TEMPLATE_COLUMNS}`;

interface SensorRowProps {
  name: string;
  repoAddress: RepoAddress;
  checked: boolean;
  onToggleChecked: (values: {checked: boolean; shiftKey: boolean}) => void;
  showCheckboxColumn: boolean;
  sensorState: BasicInstigationStateFragment;
  height: number;
  start: number;
}

export const VirtualizedSensorRow = (props: SensorRowProps) => {
  const {
    name,
    repoAddress,
    checked,
    onToggleChecked,
    showCheckboxColumn,
    sensorState,
    start,
    height,
  } = props;

  // Wait 100ms before querying in case we're scrolling the table really fast
  const shouldQuery = useDelayedState(100);

  const sensorQueryResult = useQuery<SingleSensorQuery, SingleSensorQueryVariables>(
    SINGLE_SENSOR_QUERY,
    {
      variables: {
        selector: {
          repositoryName: repoAddress.name,
          repositoryLocationName: repoAddress.location,
          sensorName: name,
        },
      },
      skip: !shouldQuery,
    },
  );

  const sensorAssetSelectionQueryResult = useQuery<
    SensorAssetSelectionQuery,
    SensorAssetSelectionQueryVariables
  >(SENSOR_ASSET_SELECTIONS_QUERY, {
    variables: {
      sensorSelector: {
        repositoryName: repoAddress.name,
        repositoryLocationName: repoAddress.location,
        sensorName: name,
      },
    },
    skip: !shouldQuery,
  });

  useQueryRefreshAtInterval(sensorQueryResult, FIFTEEN_SECONDS);
  useQueryRefreshAtInterval(sensorAssetSelectionQueryResult, FIFTEEN_SECONDS);

  const {data} = sensorQueryResult;

  const sensorData = React.useMemo(() => {
    if (data?.sensorOrError.__typename !== 'Sensor') {
      return null;
    }

    return data.sensorOrError;
  }, [data]);

  const onChange = (e: React.FormEvent<HTMLInputElement>) => {
    if (onToggleChecked && e.target instanceof HTMLInputElement) {
      const {checked} = e.target;
      const shiftKey =
        e.nativeEvent instanceof MouseEvent && e.nativeEvent.getModifierState('Shift');
      onToggleChecked({checked, shiftKey});
    }
  };

  const checkboxState = React.useMemo(() => {
    const {hasStartPermission, hasStopPermission, status} = sensorState;
    if (status === InstigationStatus.RUNNING && !hasStopPermission) {
      return {disabled: true, message: '您没有权限停止此监控器'};
    }
    if (status === InstigationStatus.STOPPED && !hasStartPermission) {
      return {disabled: true, message: '您没有权限启动此监控器'};
    }
    return {disabled: false};
  }, [sensorState]);

  const tick = sensorData?.sensorState.ticks[0];

  const sensorType = sensorData?.sensorType;
  const sensorInfo = sensorType ? SENSOR_TYPE_META[sensorType] : null;

  const selectedAssets =
    sensorAssetSelectionQueryResult.data?.sensorOrError.__typename === 'Sensor'
      ? sensorAssetSelectionQueryResult.data.sensorOrError.assetSelection
      : null;

  return (
    <Row $height={height} $start={start}>
      <RowGrid border="bottom" $showCheckboxColumn={showCheckboxColumn}>
        {showCheckboxColumn ? (
          <RowCell>
            <Tooltip
              canShow={checkboxState.disabled}
              content={checkboxState.message || ''}
              placement="top"
            >
              <Checkbox disabled={checkboxState.disabled} checked={checked} onChange={onChange} />
            </Tooltip>
          </RowCell>
        ) : null}
        <RowCell>
          <Box flex={{direction: 'column', gap: 4}}>
            <span style={{fontWeight: 500}}>
              <Link to={workspacePathFromAddress(repoAddress, `/sensors/${name}`)}>
                <MiddleTruncate text={name} />
              </Link>
            </span>
            <div
              style={{
                maxWidth: '100%',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              <Caption
                style={{
                  color: Colors.textLight(),
                  whiteSpace: 'nowrap',
                }}
              >
                {sensorData?.description}
              </Caption>
            </div>
          </Box>
        </RowCell>
        <RowCell>
          <div>
            {sensorInfo ? (
              sensorInfo.description ? (
                <Tooltip content={sensorInfo.description}>
                  <Tag icon={sensorInfo.icon}>{sensorInfo.name}</Tag>
                </Tooltip>
              ) : (
                <Tag icon={sensorInfo.icon}>{sensorInfo.name}</Tag>
              )
            ) : null}
          </div>
        </RowCell>
        <RowCell>
          {sensorData ? (
            <div>
              <AutomationTargetList
                targets={sensorData.targets}
                repoAddress={repoAddress}
                assetSelection={selectedAssets}
                automationType={sensorData.sensorType}
              />
            </div>
          ) : null}
        </RowCell>
        <RowCell>
          {sensorData ? (
            <Box flex={{direction: 'column', gap: 4}}>
              {/* Keyed so that a new switch is always rendered, otherwise it's reused and animates on/off */}
              <SensorSwitch key={name} repoAddress={repoAddress} sensor={sensorData} />
            </Box>
          ) : null}
        </RowCell>
        <RowCell>
          {sensorData ? (
            <div style={{color: Colors.textDefault()}}>
              {humanizeSensorInterval(sensorData.minIntervalSeconds)}
            </div>
          ) : (
            <LoadingOrNone queryResult={sensorQueryResult} />
          )}
        </RowCell>
        <RowCell>
          {tick ? (
            <div>
              <TickStatusTag tick={tick} tickResultType="runs" />
            </div>
          ) : (
            <LoadingOrNone queryResult={sensorQueryResult} />
          )}
        </RowCell>
        <RowCell>
          {sensorData?.sensorState && sensorData?.sensorState.runs[0] ? (
            <LastRunSummary
              run={sensorData.sensorState.runs[0]}
              name={name}
              showButton={false}
              showHover
              showSummary={false}
            />
          ) : (
            <LoadingOrNone queryResult={sensorQueryResult} />
          )}
        </RowCell>
      </RowGrid>
    </Row>
  );
};

export const VirtualizedSensorHeader = ({checkbox}: {checkbox: React.ReactNode}) => {
  return (
    <HeaderRow
      templateColumns={checkbox ? TEMPLATE_COLUMNS_WITH_CHECKBOX : TEMPLATE_COLUMNS}
      sticky
    >
      {checkbox ? (
        <HeaderCell>
          <div style={{position: 'relative', top: '-1px'}}>{checkbox}</div>
        </HeaderCell>
      ) : null}
      <HeaderCell>名称</HeaderCell>
      <HeaderCell>类型</HeaderCell>
      <HeaderCell>目标</HeaderCell>
      <HeaderCell>运行中</HeaderCell>
      <HeaderCell>频率</HeaderCell>
      <HeaderCell>上次触发</HeaderCell>
      <HeaderCell>上次运行</HeaderCell>
    </HeaderRow>
  );
};

const RowGrid = styled(Box)<{$showCheckboxColumn: boolean}>`
  display: grid;
  grid-template-columns: ${({$showCheckboxColumn}) =>
    $showCheckboxColumn ? TEMPLATE_COLUMNS_WITH_CHECKBOX : TEMPLATE_COLUMNS};
  height: 100%;
`;

export const SENSOR_TYPE_META: Record<
  SensorType,
  {name: string; icon: IconName; description: string | null}
> = {
  [SensorType.ASSET]: {
    name: '资产监控器',
    icon: 'sensors',
    description: '资产监控器在物化发生时触发运行',
  },
  [SensorType.AUTO_MATERIALIZE]: {
    name: '自动化条件监控器',
    icon: 'automation_condition',
    description: '自动化条件监控器根据资产或检查上定义的条件触发运行',
  },
  [SensorType.AUTOMATION]: {
    name: '自动化条件监控器',
    icon: 'automation_condition',
    description: '自动化条件监控器根据资产或检查上定义的条件触发运行',
  },
  [SensorType.FRESHNESS_POLICY]: {
    name: '新鲜度策略监控器',
    icon: 'sensors',
    description: '新鲜度监控器在每次触发时检查资产的新鲜度，然后根据状态执行相应操作',
  },
  [SensorType.MULTI_ASSET]: {
    name: '多资产监控器',
    icon: 'sensors',
    description: '多资产监控器根据多个资产物化事件流触发作业执行',
  },
  [SensorType.RUN_STATUS]: {
    name: '运行状态监控器',
    icon: 'sensors',
    description: '运行状态监控器对运行状态做出响应',
  },
  [SensorType.STANDARD]: {
    name: '标准监控器',
    icon: 'sensors',
    description: null,
  },
  [SensorType.UNKNOWN]: {
    name: '标准监控器',
    icon: 'sensors',
    description: null,
  },
};

export const SINGLE_SENSOR_QUERY = gql`
  query SingleSensorQuery($selector: SensorSelector!) {
    sensorOrError(sensorSelector: $selector) {
      ... on Sensor {
        id
        description
        name
        targets {
          pipelineName
        }
        metadata {
          assetKeys {
            path
          }
        }
        minIntervalSeconds
        sensorState {
          id
          runningCount
          hasStartPermission
          hasStopPermission
          ticks(limit: 1) {
            id
            ...TickTagFragment
          }
          runs(limit: 1) {
            id
            ...RunTimeFragment
          }
          nextTick {
            timestamp
          }
        }
        ...SensorSwitchFragment
      }
    }
  }

  ${TICK_TAG_FRAGMENT}
  ${RUN_TIME_FRAGMENT}
  ${SENSOR_SWITCH_FRAGMENT}
`;
