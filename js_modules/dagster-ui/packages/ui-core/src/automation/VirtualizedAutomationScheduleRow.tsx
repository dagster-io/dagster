import {useLazyQuery} from '@apollo/client';
import {Box, Caption, Checkbox, Colors, MiddleTruncate, Tooltip} from '@dagster-io/ui-components';
import {forwardRef, useMemo} from 'react';
import {Link} from 'react-router-dom';

import {AutomationRowGrid} from './VirtualizedAutomationRow';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {InstigationStatus} from '../graphql/types';
import {LastRunSummary} from '../instance/LastRunSummary';
import {useBlockTraceOnQueryResult} from '../performance/TraceContext';
import {PipelineReference} from '../pipelines/PipelineReference';
import {ScheduleSwitch} from '../schedules/ScheduleSwitch';
import {errorDisplay} from '../schedules/SchedulesTable';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {humanCronString} from '../schedules/humanCronString';
import {TickStatusTag} from '../ticks/TickStatusTag';
import {RowCell} from '../ui/VirtualizedTable';
import {SINGLE_SCHEDULE_QUERY, ScheduleStringContainer} from '../workspace/VirtualizedScheduleRow';
import {LoadingOrNone, useDelayedRowQuery} from '../workspace/VirtualizedWorkspaceTable';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
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

    const repo = useRepository(repoAddress);

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
    useBlockTraceOnQueryResult(queryResult, 'SingleScheduleQuery');

    useDelayedRowQuery(querySchedule);
    useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

    const {data} = queryResult;

    const scheduleData = useMemo(() => {
      if (data?.scheduleOrError.__typename !== 'Schedule') {
        return null;
      }

      return data.scheduleOrError;
    }, [data]);

    const isJob = !!(scheduleData && isThisThingAJob(repo, scheduleData.pipelineName));

    const cronString = scheduleData
      ? humanCronString(scheduleData.cronSchedule, scheduleData.executionTimezone || 'UTC')
      : '';

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
              {scheduleData ? (
                <Box flex={{direction: 'column', gap: 4}}>
                  {/* Keyed so that a new switch is always rendered, otherwise it's reused and animates on/off */}
                  <ScheduleSwitch key={name} repoAddress={repoAddress} schedule={scheduleData} />
                  {errorDisplay(
                    scheduleData.scheduleState.status,
                    scheduleData.scheduleState.runningCount,
                  )}
                </Box>
              ) : (
                <div style={{width: 30}} />
              )}
              <Link to={workspacePathFromAddress(repoAddress, `/schedules/${name}`)}>
                <MiddleTruncate text={name} />
              </Link>
            </Box>
          </RowCell>
          <RowCell>
            {scheduleData ? (
              <Box flex={{direction: 'column', gap: 4}}>
                <ScheduleStringContainer style={{maxWidth: '100%'}}>
                  <Tooltip position="top-left" content={scheduleData.cronSchedule} display="block">
                    <div
                      style={{
                        color: Colors.textDefault(),
                        overflow: 'hidden',
                        whiteSpace: 'nowrap',
                        maxWidth: '100%',
                        textOverflow: 'ellipsis',
                      }}
                      title={cronString}
                    >
                      {cronString}
                    </div>
                  </Tooltip>
                </ScheduleStringContainer>
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
            {scheduleData ? (
              <Caption>
                <PipelineReference
                  showIcon
                  size="small"
                  pipelineName={scheduleData.pipelineName}
                  pipelineHrefContext={repoAddress}
                  isJob={isJob}
                />
              </Caption>
            ) : null}
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
      </div>
    );
  },
);
