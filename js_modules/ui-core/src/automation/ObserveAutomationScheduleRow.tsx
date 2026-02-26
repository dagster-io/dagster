import {
  BodySmall,
  Box,
  Checkbox,
  Colors,
  HorizontalControls,
  HoverButton,
  Icon,
  ListItem,
  MetadataTable,
  MonoSmall,
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
import {RunStatusIndicator} from '../runs/RunStatusDots';
import {RunStatusOverlay} from '../runs/RunStatusPez';
import {useCronInformation} from '../schedules/CronTag';
import {SCHEDULE_ASSET_SELECTIONS_QUERY} from '../schedules/ScheduleAssetSelectionsQuery';
import {ScheduleSwitch} from '../schedules/ScheduleSwitch';
import {
  ScheduleAssetSelectionQuery,
  ScheduleAssetSelectionQueryVariables,
} from '../schedules/types/ScheduleAssetSelectionsQuery.types';
import {TimeFromNow} from '../ui/TimeFromNow';
import {SINGLE_SCHEDULE_QUERY} from '../workspace/VirtualizedScheduleRow';
import {RepoAddress} from '../workspace/types';
import {
  SingleScheduleQuery,
  SingleScheduleQueryVariables,
} from '../workspace/types/VirtualizedScheduleRow.types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

interface ScheduleRowProps {
  index: number;
  name: string;
  repoAddress: RepoAddress;
  checked: boolean;
  onToggleChecked: (values: {checked: boolean; shiftKey: boolean}) => void;
}

export const ObserveAutomationScheduleRow = forwardRef(
  (props: ScheduleRowProps, ref: ForwardedRef<HTMLDivElement>) => {
    const {index, name, repoAddress, checked, onToggleChecked} = props;

    // Wait 100ms before querying in case we're scrolling the table really fast
    const shouldQuery = useDelayedState(100);

    const queryResult = useQuery<SingleScheduleQuery, SingleScheduleQueryVariables>(
      SINGLE_SCHEDULE_QUERY,
      {
        variables: {
          selector: {
            repositoryName: repoAddress.name,
            repositoryLocationName: repoAddress.location,
            scheduleName: name,
          },
        },
        skip: !shouldQuery,
        notifyOnNetworkStatusChange: true,
      },
    );

    const scheduleAssetSelectionQueryResult = useQuery<
      ScheduleAssetSelectionQuery,
      ScheduleAssetSelectionQueryVariables
    >(SCHEDULE_ASSET_SELECTIONS_QUERY, {
      variables: {
        scheduleSelector: {
          repositoryName: repoAddress.name,
          repositoryLocationName: repoAddress.location,
          scheduleName: name,
        },
      },
      skip: !shouldQuery,
    });

    useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
    useQueryRefreshAtInterval(scheduleAssetSelectionQueryResult, FIFTEEN_SECONDS);

    const {data} = queryResult;

    const scheduleData = useMemo(() => {
      if (data?.scheduleOrError.__typename !== 'Schedule') {
        return null;
      }

      return data.scheduleOrError;
    }, [data]);

    const tick = scheduleData?.scheduleState.ticks[0];

    const {withHumanTimezone, withExecutionTimezone} = useCronInformation(
      scheduleData?.cronSchedule ?? null,
      scheduleData?.executionTimezone ?? null,
    );

    const right = () => {
      if (queryResult.loading && !queryResult.data) {
        return <Skeleton $width={200} $height={24} />;
      }

      const latestRuns = scheduleData?.scheduleState.runs || [];

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
                  {scheduleData ? (
                    <ScheduleSwitch key={name} repoAddress={repoAddress} schedule={scheduleData} />
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
        href={workspacePathFromAddress(repoAddress, `/schedules/${name}`)}
        checked={checked}
        onToggle={onToggleChecked}
        renderLink={({href, ...props}) => <Link to={href || '#'} {...props} />}
        left={
          <Box flex={{direction: 'row', gap: 8, alignItems: 'flex-start'}}>
            <div>
              <Icon name="schedule" />
            </div>
            <Box flex={{direction: 'column', gap: 4}}>
              <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
                <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>{name}</Box>
                {scheduleData?.description ? (
                  <Tooltip
                    content={<div style={{maxWidth: 320}}>{scheduleData.description}</div>}
                    placement="top"
                  >
                    <Icon name="info" color={Colors.textLight()} />
                  </Tooltip>
                ) : null}
              </Box>
              {withHumanTimezone ? (
                <BodySmall>
                  Scheduled{' '}
                  <Tooltip
                    placement="top"
                    content={
                      <MetadataTable
                        rows={[
                          {
                            key: 'Cron value',
                            value: <MonoSmall>{scheduleData?.cronSchedule ?? ''}</MonoSmall>,
                          },
                          {key: 'Your time', value: <span>{withHumanTimezone}</span>},
                        ]}
                      />
                    }
                  >
                    <span>{withExecutionTimezone}</span>
                  </Tooltip>
                </BodySmall>
              ) : (
                <Skeleton $width={80} $height={16} />
              )}
            </Box>
          </Box>
        }
        right={right()}
      />
    );
  },
);

ObserveAutomationScheduleRow.displayName = 'ObserveAutomationScheduleRow';
