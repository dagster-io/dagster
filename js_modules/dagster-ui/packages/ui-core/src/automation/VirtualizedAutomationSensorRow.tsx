import {Box, Button, Checkbox, MiddleTruncate, Tag, Tooltip} from '@dagster-io/ui-components';
import {forwardRef, useCallback, useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import {AutomationTargetList} from './AutomationTargetList';
import {AutomationRowGrid} from './VirtualizedAutomationRow';
import {useLazyQuery} from '../apollo-client';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {InstigationStatus, SensorType} from '../graphql/types';
import {LastRunSummary} from '../instance/LastRunSummary';
import {SENSOR_ASSET_SELECTIONS_QUERY} from '../sensors/SensorRoot';
import {SensorSwitch} from '../sensors/SensorSwitch';
import {
  SensorAssetSelectionQuery,
  SensorAssetSelectionQueryVariables,
} from '../sensors/types/SensorRoot.types';
import {SensorDryRunDialog} from '../ticks/SensorDryRunDialog';
import {TickStatusTag} from '../ticks/TickStatusTag';
import {RowCell} from '../ui/VirtualizedTable';
import {SENSOR_TYPE_META, SINGLE_SENSOR_QUERY} from '../workspace/VirtualizedSensorRow';
import {LoadingOrNone, useDelayedRowQuery} from '../workspace/VirtualizedWorkspaceTable';
import {RepoAddress} from '../workspace/types';
import {
  SingleSensorQuery,
  SingleSensorQueryVariables,
} from '../workspace/types/VirtualizedSensorRow.types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface Props {
  index: number;
  name: string;
  repoAddress: RepoAddress;
  checked: boolean;
  onToggleChecked: (values: {checked: boolean; shiftKey: boolean}) => void;
}

export const VirtualizedAutomationSensorRow = forwardRef(
  (props: Props, ref: React.ForwardedRef<HTMLDivElement>) => {
    const {index, name, repoAddress, checked, onToggleChecked} = props;

    const [showTestTickDialog, setShowTestTickDialog] = useState(false);

    const [querySensor, sensorQueryResult] = useLazyQuery<
      SingleSensorQuery,
      SingleSensorQueryVariables
    >(SINGLE_SENSOR_QUERY, {
      variables: {
        selector: {
          repositoryName: repoAddress.name,
          repositoryLocationName: repoAddress.location,
          sensorName: name,
        },
      },
    });

    const [querySensorAssetSelection, sensorAssetSelectionQueryResult] = useLazyQuery<
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
    });

    useDelayedRowQuery(
      useCallback(() => {
        querySensor();
        querySensorAssetSelection();
      }, [querySensor, querySensorAssetSelection]),
    );

    useQueryRefreshAtInterval(sensorQueryResult, FIFTEEN_SECONDS);
    useQueryRefreshAtInterval(sensorAssetSelectionQueryResult, FIFTEEN_SECONDS);

    const {data} = sensorQueryResult;

    const sensorData = useMemo(() => {
      if (data?.sensorOrError.__typename !== 'Sensor') {
        return null;
      }

      return data.sensorOrError;
    }, [data]);

    const cursor =
      sensorData &&
      sensorData.sensorState.typeSpecificData &&
      sensorData.sensorState.typeSpecificData.__typename === 'SensorData' &&
      sensorData.sensorState.typeSpecificData.lastCursor;

    const onChange = (e: React.FormEvent<HTMLInputElement>) => {
      if (onToggleChecked && e.target instanceof HTMLInputElement) {
        const {checked} = e.target;
        const shiftKey =
          e.nativeEvent instanceof MouseEvent && e.nativeEvent.getModifierState('Shift');
        onToggleChecked({checked, shiftKey});
      }
    };

    const sensorState = sensorData?.sensorState;

    const checkboxState = useMemo(() => {
      if (!sensorState) {
        return {disabled: true};
      }

      const {hasStartPermission, hasStopPermission, status} = sensorState;
      if (status === InstigationStatus.RUNNING && !hasStopPermission) {
        return {disabled: true, message: 'You do not have permission to stop this sensor'};
      }
      if (status === InstigationStatus.STOPPED && !hasStartPermission) {
        return {disabled: true, message: 'You do not have permission to start this sensor'};
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
      <div ref={ref} data-index={index}>
        <AutomationRowGrid border="bottom">
          <RowCell>
            <Tooltip
              canShow={checkboxState.disabled}
              content={checkboxState.message || ''}
              placement="top"
            >
              <Checkbox disabled={checkboxState.disabled} checked={checked} onChange={onChange} />
            </Tooltip>
          </RowCell>
          <RowCell>
            <Box flex={{direction: 'row', gap: 8, alignItems: 'flex-start'}}>
              {/* Left aligned content */}
              <Box flex={{grow: 1, gap: 8}}>
                {/* Keyed so that a new switch is always rendered, otherwise it's reused and animates on/off */}
                {sensorData ? (
                  <SensorSwitch key={name} repoAddress={repoAddress} sensor={sensorData} />
                ) : (
                  <div style={{width: 30}} />
                )}
                <Link to={workspacePathFromAddress(repoAddress, `/sensors/${name}`)}>
                  <MiddleTruncate text={name} />
                </Link>
              </Box>
              {/* Right aligned content */}
              {sensorData ? (
                <Tooltip
                  canShow={sensorData.sensorType !== SensorType.STANDARD}
                  content="Testing not available for this sensor type"
                  placement="top-end"
                >
                  <Button
                    disabled={sensorData.sensorType !== SensorType.STANDARD}
                    onClick={() => {
                      setShowTestTickDialog(true);
                    }}
                    style={{height: '24px', marginTop: '-4px'}} // center button text with content in AutomationRowGrid
                  >
                    Manual tick
                  </Button>
                </Tooltip>
              ) : (
                <div style={{width: 30}} />
              )}
            </Box>
          </RowCell>
          <RowCell>
            <div>
              {sensorInfo ? (
                sensorInfo.description ? (
                  <Tooltip
                    content={<div style={{maxWidth: '300px'}}>{sensorInfo.description}</div>}
                    placement="top"
                  >
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
                  targets={sensorData.targets || null}
                  repoAddress={repoAddress}
                  assetSelection={selectedAssets}
                  automationType={sensorData.sensorType}
                />
              </div>
            ) : (
              <LoadingOrNone queryResult={sensorAssetSelectionQueryResult} />
            )}
          </RowCell>
          <RowCell>
            {tick ? (
              <div>
                <TickStatusTag tick={tick} />
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
        </AutomationRowGrid>
        <SensorDryRunDialog
          isOpen={showTestTickDialog}
          onClose={() => {
            setShowTestTickDialog(false);
          }}
          currentCursor={cursor || ''}
          name={sensorData?.name || ''}
          repoAddress={repoAddress}
          jobName={sensorData?.targets?.[0]?.pipelineName || ''}
        />
      </div>
    );
  },
);
