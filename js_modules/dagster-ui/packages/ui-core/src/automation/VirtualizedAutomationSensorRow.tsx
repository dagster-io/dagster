import {
  Box,
  Checkbox,
  MiddleTruncate,
  Tag,
  Tooltip,
  useDelayedState,
} from '@dagster-io/ui-components';
import {forwardRef, useMemo} from 'react';
import {Link} from 'react-router-dom';

import {AutomationTargetList} from './AutomationTargetList';
import {AutomationRowGrid} from './VirtualizedAutomationRow';
import {useQuery} from '../apollo-client';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {InstigationStatus} from '../graphql/types';
import {LastRunSummary} from '../instance/LastRunSummary';
import {SENSOR_ASSET_SELECTIONS_QUERY} from '../sensors/SensorRoot';
import {SensorSwitch} from '../sensors/SensorSwitch';
import {
  SensorAssetSelectionQuery,
  SensorAssetSelectionQueryVariables,
} from '../sensors/types/SensorRoot.types';
import {TickStatusTag} from '../ticks/TickStatusTag';
import {RowCell} from '../ui/VirtualizedTable';
import {SENSOR_TYPE_META, SINGLE_SENSOR_QUERY} from '../workspace/VirtualizedSensorRow';
import {LoadingOrNone} from '../workspace/VirtualizedWorkspaceTable';
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

    const sensorData = useMemo(() => {
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
            <Box
              flex={{
                direction: 'row',
                gap: 8,
                alignItems: 'flex-start',
                justifyContent: 'space-between',
              }}
            >
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
        </AutomationRowGrid>
      </div>
    );
  },
);
