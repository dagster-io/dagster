import {
  BodySmall,
  Box,
  Checkbox,
  Colors,
  HorizontalControls,
  HoverButton,
  Icon,
  ListItem,
  Popover,
  Skeleton,
  Tooltip,
  useDelayedState,
} from '@dagster-io/ui-components';
import {ForwardedRef, forwardRef, useMemo} from 'react';
import {Link} from 'react-router-dom';

import {LatestTickHoverButton} from './LatestTickHoverButton';
import {useQuery} from '../apollo-client';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {SensorType} from '../graphql/types';
import {RunStatusIndicator} from '../runs/RunStatusDots';
import {RunStatusOverlay} from '../runs/RunStatusPez';
import {SENSOR_ASSET_SELECTIONS_QUERY} from '../sensors/SensorRoot';
import {SensorSwitch} from '../sensors/SensorSwitch';
import {
  SensorAssetSelectionQuery,
  SensorAssetSelectionQueryVariables,
} from '../sensors/types/SensorRoot.types';
import {TimeFromNow} from '../ui/TimeFromNow';
import {SENSOR_TYPE_META, SINGLE_SENSOR_QUERY} from '../workspace/VirtualizedSensorRow';
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

export const ObserveAutomationSensorRow = forwardRef(
  (props: Props, ref: ForwardedRef<HTMLDivElement>) => {
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

    const tick = sensorData?.sensorState.ticks[0];

    const sensorType = sensorData?.sensorType;
    const sensorInfo = sensorType ? SENSOR_TYPE_META[sensorType] : null;

    const right = () => {
      if (sensorQueryResult.loading && !sensorQueryResult.data) {
        return <Skeleton $width={200} $height={24} />;
      }

      const latestRuns = sensorData?.sensorState.runs || [];

      return (
        <HorizontalControls
          controls={[
            {
              key: 'latest-run',
              control: latestRuns[0]?.startTime ? (
                <Popover
                  key={latestRuns[0].id}
                  position="top"
                  interactionKind="hover"
                  content={
                    <div>
                      <RunStatusOverlay run={latestRuns[0]} name={name} />
                    </div>
                  }
                  hoverOpenDelay={100}
                >
                  <HoverButton>
                    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
                      <RunStatusIndicator status={latestRuns[0].status} />
                      <TimeFromNow unixTimestamp={latestRuns[0].startTime} showTooltip={false} />
                    </Box>
                  </HoverButton>
                </Popover>
              ) : null,
            },
            {
              key: 'tick',
              control: <LatestTickHoverButton tick={tick ?? null} />,
            },
            {
              key: 'switch',
              control: (
                <Box flex={{direction: 'column', justifyContent: 'center'}} padding={{left: 8}}>
                  {sensorData ? (
                    <SensorSwitch key={name} repoAddress={repoAddress} sensor={sensorData} />
                  ) : (
                    <Checkbox key={name} disabled indeterminate checked={false} format="switch" />
                  )}
                </Box>
              ),
            },
          ]}
        />
      );
    };

    return (
      <ListItem
        ref={ref}
        index={index}
        href={workspacePathFromAddress(repoAddress, `/sensors/${name}`)}
        checked={checked}
        onToggle={onToggleChecked}
        renderLink={({href, ...props}) => <Link to={href || '#'} {...props} />}
        left={
          <Box flex={{direction: 'row', gap: 8, alignItems: 'flex-start'}}>
            <div>
              <Icon name="sensors" />
            </div>
            <Box flex={{direction: 'column', gap: 4}}>
              <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
                {name}
                {sensorInfo?.description ? (
                  <Tooltip
                    content={<div style={{width: 320}}>{sensorInfo.description}</div>}
                    placement="top"
                  >
                    <Icon name="info" color={Colors.textLight()} />
                  </Tooltip>
                ) : null}
              </Box>
              <BodySmall>
                {sensorData?.sensorType ? (
                  sensorTypeToLabel[sensorData.sensorType]
                ) : (
                  <Skeleton $width={80} $height={16} />
                )}
              </BodySmall>
            </Box>
          </Box>
        }
        right={right()}
      />
    );
  },
);

ObserveAutomationSensorRow.displayName = 'ObserveAutomationSensorRow';

const sensorTypeToLabel: Record<SensorType, string> = {
  [SensorType.ASSET]: 'Asset sensor',
  [SensorType.AUTOMATION]: 'Automation condition sensor',
  [SensorType.AUTO_MATERIALIZE]: 'Automation condition sensor',
  [SensorType.FRESHNESS_POLICY]: 'Freshness policy sensor',
  [SensorType.MULTI_ASSET]: 'Multi-asset sensor',
  [SensorType.RUN_STATUS]: 'Run status sensor',
  [SensorType.STANDARD]: 'Standard sensor',
  [SensorType.UNKNOWN]: 'Unknown sensor type',
};
