import {Box, Button, Caption, Checkbox, MiddleTruncate, Tooltip} from '@dagster-io/ui-components';
import {forwardRef, useCallback, useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import {AutomationTargetList} from './AutomationTargetList';
import {AutomationRowGrid} from './VirtualizedAutomationRow';
import {useLazyQuery} from '../apollo-client';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {InstigationStatus} from '../graphql/types';
import {LastRunSummary} from '../instance/LastRunSummary';
import {CronTag} from '../schedules/CronTag';
import {SCHEDULE_ASSET_SELECTIONS_QUERY} from '../schedules/ScheduleAssetSelectionsQuery';
import {ScheduleSwitch} from '../schedules/ScheduleSwitch';
import {errorDisplay} from '../schedules/SchedulesTable';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {
  ScheduleAssetSelectionQuery,
  ScheduleAssetSelectionQueryVariables,
} from '../schedules/types/ScheduleAssetSelectionsQuery.types';
import {EvaluateScheduleDialog} from '../ticks/EvaluateScheduleDialog';
import {TickStatusTag} from '../ticks/TickStatusTag';
import {RowCell} from '../ui/VirtualizedTable';
import {SINGLE_SCHEDULE_QUERY} from '../workspace/VirtualizedScheduleRow';
import {LoadingOrNone, useDelayedRowQuery} from '../workspace/VirtualizedWorkspaceTable';
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

export const VirtualizedAutomationScheduleRow = forwardRef(
  (props: ScheduleRowProps, ref: React.ForwardedRef<HTMLDivElement>) => {
    const {index, name, repoAddress, checked, onToggleChecked} = props;

    const [showTestTickDialog, setShowTestTickDialog] = useState(false);

    const [querySchedule, queryResult] = useLazyQuery<
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
      useCallback(() => {
        querySchedule();
        queryScheduleAssetSelection();
      }, [querySchedule, queryScheduleAssetSelection]),
    );

    useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
    useQueryRefreshAtInterval(scheduleAssetSelectionQueryResult, FIFTEEN_SECONDS);

    const {data} = queryResult;

    const scheduleData = useMemo(() => {
      if (data?.scheduleOrError.__typename !== 'Schedule') {
        return null;
      }

      return data.scheduleOrError;
    }, [data]);

    const onChange = (e: React.FormEvent<HTMLInputElement>) => {
      if (onToggleChecked && e.target instanceof HTMLInputElement) {
        const {checked} = e.target;
        const shiftKey =
          e.nativeEvent instanceof MouseEvent && e.nativeEvent.getModifierState('Shift');
        onToggleChecked({checked, shiftKey});
      }
    };

    const scheduleState = scheduleData?.scheduleState;

    const checkboxState = useMemo(() => {
      if (!scheduleState) {
        return {disabled: true};
      }

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
            {/* Left aligned content */}
            <Box flex={{direction: 'row', gap: 8, alignItems: 'flex-start'}}>
              <Box flex={{grow: 1, gap: 8}}>
                {scheduleData ? (
                  <>
                    <ScheduleSwitch key={name} repoAddress={repoAddress} schedule={scheduleData} />
                    {errorDisplay(
                      scheduleData.scheduleState.status,
                      scheduleData.scheduleState.runningCount,
                    )}
                  </>
                ) : (
                  <div style={{width: 30}} />
                )}
                <Link to={workspacePathFromAddress(repoAddress, `/schedules/${name}`)}>
                  <MiddleTruncate text={name} />
                </Link>
              </Box>
              {/* Right aligned content */}
              <Button
                onClick={() => {
                  setShowTestTickDialog(true);
                }}
                style={{height: '24px', marginTop: '-4px'}} // center button text with content in AutomationRowGrid
              >
                Manual tick
              </Button>
            </Box>
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
              <LoadingOrNone queryResult={queryResult} />
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
            {tick ? (
              <div>
                <TickStatusTag tick={tick} />
              </div>
            ) : (
              <LoadingOrNone queryResult={queryResult} />
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
              <LoadingOrNone queryResult={queryResult} />
            )}
          </RowCell>
        </AutomationRowGrid>
        <EvaluateScheduleDialog
          key={showTestTickDialog ? '1' : '0'} // change key to reset dialog state
          isOpen={showTestTickDialog}
          onClose={() => {
            setShowTestTickDialog(false);
          }}
          name={scheduleData?.name || ''}
          repoAddress={repoAddress}
          jobName={scheduleData?.pipelineName || ''}
        />
      </div>
    );
  },
);
