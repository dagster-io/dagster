import {
  Box,
  Button,
  Caption,
  Checkbox,
  Colors,
  Icon,
  Menu,
  MiddleTruncate,
  Popover,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {LoadingOrNone, useDelayedRowQuery} from './VirtualizedWorkspaceTable';
import {isThisThingAJob, useRepository} from './WorkspaceContext/util';
import {RepoAddress} from './types';
import {
  SingleScheduleQuery,
  SingleScheduleQueryVariables,
} from './types/VirtualizedScheduleRow.types';
import {workspacePathFromAddress} from './workspacePath';
import {gql, useLazyQuery} from '../apollo-client';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {AutomationTargetList} from '../automation/AutomationTargetList';
import {InstigationStatus} from '../graphql/types';
import {LastRunSummary} from '../instance/LastRunSummary';
import {TICK_TAG_FRAGMENT} from '../instigation/InstigationTick';
import {BasicInstigationStateFragment} from '../overview/types/BasicInstigationStateFragment.types';
import {RUN_TIME_FRAGMENT} from '../runs/RunUtils';
import {CronTag} from '../schedules/CronTag';
import {SCHEDULE_ASSET_SELECTIONS_QUERY} from '../schedules/ScheduleAssetSelectionsQuery';
import {SCHEDULE_SWITCH_FRAGMENT, ScheduleSwitch} from '../schedules/ScheduleSwitch';
import {errorDisplay} from '../schedules/SchedulesTable';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {
  ScheduleAssetSelectionQuery,
  ScheduleAssetSelectionQueryVariables,
} from '../schedules/types/ScheduleAssetSelectionsQuery.types';
import {TickStatusTag} from '../ticks/TickStatusTag';
import {MenuLink} from '../ui/MenuLink';
import {HeaderCell, HeaderRow, Row, RowCell} from '../ui/VirtualizedTable';

const TEMPLATE_COLUMNS = '1.2fr 1fr 1fr 76px 148px 210px 92px';
const TEMPLATE_COLUMNS_WITH_CHECKBOX = `60px ${TEMPLATE_COLUMNS}`;

interface ScheduleRowProps {
  name: string;
  repoAddress: RepoAddress;
  checked: boolean;
  onToggleChecked: (values: {checked: boolean; shiftKey: boolean}) => void;
  showCheckboxColumn: boolean;
  scheduleState: BasicInstigationStateFragment;
  height: number;
  start: number;
}

export const VirtualizedScheduleRow = (props: ScheduleRowProps) => {
  const {
    name,
    repoAddress,
    checked,
    onToggleChecked,
    showCheckboxColumn,
    scheduleState,
    start,
    height,
  } = props;

  const repo = useRepository(repoAddress);

  const [querySchedule, scheduleQueryResult] = useLazyQuery<
    SingleScheduleQuery,
    SingleScheduleQueryVariables
  >(SINGLE_SCHEDULE_QUERY, {
    variables: {
      selector: {
        repositoryName: repoAddress.name,
        repositoryLocationName: repoAddress.location,
        scheduleName: name,
      },
    },
    notifyOnNetworkStatusChange: true,
  });

  const [queryScheduleAssetSelection, scheduleAssetSelectionQueryResult] = useLazyQuery<
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
  });

  useDelayedRowQuery(
    React.useCallback(() => {
      querySchedule();
      queryScheduleAssetSelection();
    }, [querySchedule, queryScheduleAssetSelection]),
  );

  useQueryRefreshAtInterval(scheduleQueryResult, FIFTEEN_SECONDS);
  useQueryRefreshAtInterval(scheduleAssetSelectionQueryResult, FIFTEEN_SECONDS);

  const {data} = scheduleQueryResult;

  const scheduleData = React.useMemo(() => {
    if (data?.scheduleOrError.__typename !== 'Schedule') {
      return null;
    }

    return data.scheduleOrError;
  }, [data]);

  const isJob = !!(scheduleData && isThisThingAJob(repo, scheduleData.pipelineName));

  const onChange = (e: React.FormEvent<HTMLInputElement>) => {
    if (onToggleChecked && e.target instanceof HTMLInputElement) {
      const {checked} = e.target;
      const shiftKey =
        e.nativeEvent instanceof MouseEvent && e.nativeEvent.getModifierState('Shift');
      onToggleChecked({checked, shiftKey});
    }
  };

  const checkboxState = React.useMemo(() => {
    const {hasStartPermission, hasStopPermission, status} = scheduleState;
    if (status === InstigationStatus.RUNNING && !hasStopPermission) {
      return {disabled: true, message: 'You do not have permission to stop this schedule'};
    }
    if (status === InstigationStatus.STOPPED && !hasStartPermission) {
      return {disabled: true, message: 'You do not have permission to start this schedule'};
    }
    return {disabled: false};
  }, [scheduleState]);

  const tick = scheduleData?.scheduleState.ticks[0];
  const targets = scheduleData?.pipelineName ? [{pipelineName: scheduleData.pipelineName}] : null;
  const assetSelection =
    scheduleAssetSelectionQueryResult.data?.scheduleOrError.__typename === 'Schedule'
      ? scheduleAssetSelectionQueryResult.data.scheduleOrError.assetSelection
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
          <span style={{fontWeight: 500}}>
            <Link to={workspacePathFromAddress(repoAddress, `/schedules/${name}`)}>
              <MiddleTruncate text={name} />
            </Link>
          </span>
        </RowCell>
        <RowCell>
          {scheduleData ? (
            <Box flex={{direction: 'column', gap: 4}}>
              <CronTag
                cronSchedule={scheduleData.cronSchedule}
                executionTimezone={scheduleData.executionTimezone}
              />
              {scheduleData.scheduleState.nextTick &&
              scheduleData.scheduleState.status === InstigationStatus.RUNNING ? (
                <Caption>
                  <div
                    style={{
                      overflow: 'hidden',
                      whiteSpace: 'nowrap',
                      maxWidth: '100%',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    Next tick:&nbsp;
                    <TimestampDisplay
                      timestamp={scheduleData.scheduleState.nextTick.timestamp!}
                      timezone={scheduleData.executionTimezone}
                      timeFormat={{showSeconds: false, showTimezone: true}}
                    />
                  </div>
                </Caption>
              ) : null}
            </Box>
          ) : (
            <LoadingOrNone queryResult={scheduleQueryResult} />
          )}
        </RowCell>
        <RowCell>
          <div>
            <AutomationTargetList
              repoAddress={repoAddress}
              automationType="schedule"
              targets={targets}
              assetSelection={assetSelection}
            />
          </div>
        </RowCell>
        <RowCell>
          {scheduleData ? (
            <Box flex={{direction: 'column', gap: 4}}>
              {/* Keyed so that a new switch is always rendered, otherwise it's reused and animates on/off */}
              <ScheduleSwitch key={name} repoAddress={repoAddress} schedule={scheduleData} />
              {errorDisplay(
                scheduleData.scheduleState.status,
                scheduleData.scheduleState.runningCount,
              )}
            </Box>
          ) : null}
        </RowCell>
        <RowCell>
          {tick ? (
            <div>
              <TickStatusTag tick={tick} tickResultType="runs" />
            </div>
          ) : (
            <LoadingOrNone queryResult={scheduleQueryResult} />
          )}
        </RowCell>
        <RowCell>
          {scheduleData?.scheduleState && scheduleData?.scheduleState.runs[0] ? (
            <LastRunSummary
              run={scheduleData.scheduleState.runs[0]}
              name={name}
              showButton={false}
              showHover
              showSummary={false}
            />
          ) : (
            <LoadingOrNone queryResult={scheduleQueryResult} />
          )}
        </RowCell>
        <RowCell>
          {scheduleData?.partitionSet ? (
            <Popover
              content={
                <Menu>
                  <MenuLink
                    text="View partition history"
                    icon="dynamic_feed"
                    target="_blank"
                    to={workspacePathFromAddress(
                      repoAddress,
                      `/${isJob ? 'jobs' : 'pipelines'}/${scheduleData.pipelineName}/partitions`,
                    )}
                  />
                  <MenuLink
                    text="Launch partition backfill"
                    icon="add_circle"
                    target="_blank"
                    to={workspacePathFromAddress(
                      repoAddress,
                      `/${isJob ? 'jobs' : 'pipelines'}/${scheduleData.pipelineName}/partitions`,
                    )}
                  />
                </Menu>
              }
              position="bottom-left"
            >
              <Button icon={<Icon name="expand_more" />} />
            </Popover>
          ) : (
            <span style={{color: Colors.textLight()}}>{'\u2013'}</span>
          )}
        </RowCell>
      </RowGrid>
    </Row>
  );
};

export const VirtualizedScheduleHeader = (props: {checkbox: React.ReactNode}) => {
  const {checkbox} = props;
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
      <HeaderCell>Schedule name</HeaderCell>
      <HeaderCell>Schedule</HeaderCell>
      <HeaderCell>Target</HeaderCell>
      <HeaderCell>Running</HeaderCell>
      <HeaderCell>Last tick</HeaderCell>
      <HeaderCell>Last run</HeaderCell>
      <HeaderCell>Actions</HeaderCell>
    </HeaderRow>
  );
};

const RowGrid = styled(Box)<{$showCheckboxColumn: boolean}>`
  display: grid;
  grid-template-columns: ${({$showCheckboxColumn}) =>
    $showCheckboxColumn ? TEMPLATE_COLUMNS_WITH_CHECKBOX : TEMPLATE_COLUMNS};
  height: 100%;
`;

export const SINGLE_SCHEDULE_QUERY = gql`
  query SingleScheduleQuery($selector: ScheduleSelector!) {
    scheduleOrError(scheduleSelector: $selector) {
      ... on Schedule {
        id
        name
        pipelineName
        description
        scheduleState {
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
        partitionSet {
          id
          name
        }
        ...ScheduleSwitchFragment
      }
    }
  }

  ${TICK_TAG_FRAGMENT}
  ${RUN_TIME_FRAGMENT}
  ${SCHEDULE_SWITCH_FRAGMENT}
`;
