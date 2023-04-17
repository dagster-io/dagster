import {gql, useLazyQuery} from '@apollo/client';
import {Box, Caption, Checkbox, Colors, MiddleTruncate, Tooltip} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {useQueryRefreshAtInterval, FIFTEEN_SECONDS} from '../app/QueryRefresh';
import {AssetLink} from '../assets/AssetLink';
import {InstigationStatus, InstigationType} from '../graphql/types';
import {LastRunSummary} from '../instance/LastRunSummary';
import {TickTag, TICK_TAG_FRAGMENT} from '../instigation/InstigationTick';
import {BasicInstigationStateFragment} from '../overview/types/BasicInstigationStateFragment.types';
import {PipelineReference} from '../pipelines/PipelineReference';
import {RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {humanizeSensorInterval} from '../sensors/SensorDetails';
import {SensorSwitch, SENSOR_SWITCH_FRAGMENT} from '../sensors/SensorSwitch';
import {HeaderCell, Row, RowCell} from '../ui/VirtualizedTable';

import {LoadingOrNone, useDelayedRowQuery} from './VirtualizedWorkspaceTable';
import {isThisThingAJob, useRepository} from './WorkspaceContext';
import {RepoAddress} from './types';
import {SingleSensorQuery, SingleSensorQueryVariables} from './types/VirtualizedSensorRow.types';
import {workspacePathFromAddress} from './workspacePath';

const TEMPLATE_COLUMNS_WITH_CHECKBOX = '60px 1.5fr 1fr 76px 120px 148px 180px';
const TEMPLATE_COLUMNS = '1.5fr 1fr 76px 120px 148px 180px';

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

  const repo = useRepository(repoAddress);

  const [querySensor, queryResult] = useLazyQuery<SingleSensorQuery, SingleSensorQueryVariables>(
    SINGLE_SENSOR_QUERY,
    {
      variables: {
        selector: {
          repositoryName: repoAddress.name,
          repositoryLocationName: repoAddress.location,
          sensorName: name,
        },
      },
    },
  );

  useDelayedRowQuery(querySensor);
  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const {data} = queryResult;

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
      return {disabled: true, message: 'You do not have permission to stop this sensor'};
    }
    if (status === InstigationStatus.STOPPED && !hasStartPermission) {
      return {disabled: true, message: 'You do not have permission to start this sensor'};
    }
    return {disabled: false};
  }, [sensorState]);

  return (
    <Row $height={height} $start={start}>
      <RowGrid
        border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
        $showCheckboxColumn={showCheckboxColumn}
      >
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
                  color: Colors.Gray500,
                  whiteSpace: 'nowrap',
                }}
              >
                {sensorData?.description}
              </Caption>
            </div>
          </Box>
        </RowCell>
        <RowCell>
          <Box flex={{direction: 'column', gap: 4}} style={{fontSize: '12px'}}>
            {sensorData?.targets && sensorData.targets.length ? (
              <Box flex={{direction: 'column', gap: 2}}>
                {sensorData.targets.map((target) => (
                  <PipelineReference
                    key={target.pipelineName}
                    showIcon
                    size="small"
                    pipelineName={target.pipelineName}
                    pipelineHrefContext={repoAddress}
                    isJob={!!(repo && isThisThingAJob(repo, target.pipelineName))}
                  />
                ))}
              </Box>
            ) : null}
            {sensorData?.metadata.assetKeys && sensorData.metadata.assetKeys.length ? (
              <Box flex={{direction: 'column', gap: 2}}>
                {sensorData.metadata.assetKeys.map((key) => (
                  <AssetLink key={key.path.join('/')} path={key.path} icon="asset" />
                ))}
              </Box>
            ) : null}
          </Box>
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
            <div style={{color: Colors.Dark}}>
              {humanizeSensorInterval(sensorData.minIntervalSeconds)}
            </div>
          ) : (
            <LoadingOrNone queryResult={queryResult} />
          )}
        </RowCell>
        <RowCell>
          {sensorData?.sensorState.ticks.length ? (
            <div>
              <TickTag
                tick={sensorData.sensorState.ticks[0]}
                instigationType={InstigationType.SENSOR}
              />
            </div>
          ) : (
            <LoadingOrNone queryResult={queryResult} />
          )}
        </RowCell>
        <RowCell>
          {sensorData?.sensorState && sensorData?.sensorState.runs.length > 0 ? (
            <LastRunSummary
              run={sensorData.sensorState.runs[0]}
              name={name}
              showButton={false}
              showHover
              showSummary={false}
            />
          ) : (
            <LoadingOrNone queryResult={queryResult} />
          )}
        </RowCell>
      </RowGrid>
    </Row>
  );
};

export const VirtualizedSensorHeader = (props: {checkbox: React.ReactNode}) => {
  const {checkbox} = props;
  return (
    <Box
      border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
      style={{
        display: 'grid',
        gridTemplateColumns: checkbox ? TEMPLATE_COLUMNS_WITH_CHECKBOX : TEMPLATE_COLUMNS,
        height: '32px',
        fontSize: '12px',
        color: Colors.Gray600,
      }}
    >
      {checkbox ? (
        <HeaderCell>
          <div style={{position: 'relative', top: '-1px'}}>{checkbox}</div>
        </HeaderCell>
      ) : null}
      <HeaderCell>Name</HeaderCell>
      <HeaderCell>Job / Asset</HeaderCell>
      <HeaderCell>Running</HeaderCell>
      <HeaderCell>Frequency</HeaderCell>
      <HeaderCell>Last tick</HeaderCell>
      <HeaderCell>Last run</HeaderCell>
    </Box>
  );
};

const RowGrid = styled(Box)<{$showCheckboxColumn: boolean}>`
  display: grid;
  grid-template-columns: ${({$showCheckboxColumn}) =>
    $showCheckboxColumn ? TEMPLATE_COLUMNS_WITH_CHECKBOX : TEMPLATE_COLUMNS};
  height: 100%;
`;

const SINGLE_SENSOR_QUERY = gql`
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
        description
        sensorState {
          id
          runningCount
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
