import {
  Box,
  Colors,
  HorizontalControls,
  HoverButton,
  Icon,
  ListItem,
  MiddleTruncate,
  Popover,
  Skeleton,
  Tooltip,
  useDelayedState,
} from '@dagster-io/ui-components';
import {forwardRef, useMemo} from 'react';
import {Link} from 'react-router-dom';

import {SINGLE_JOB_QUERY} from './SingleJobQuery';
import {TimeFromNow} from '../ui/TimeFromNow';
import {SingleJobQuery, SingleJobQueryVariables} from './types/SingleJobQuery.types';
import {JobMenu} from '../instance/JobMenu';
import {RunStatusOverlay, RunStatusPezList} from '../runs/RunStatusPez';
import {buildPipelineSelector} from './WorkspaceContext/util';
import {RepoAddress} from './types';
import {workspacePathFromAddress} from './workspacePath';
import {useQuery} from '../apollo-client';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../app/QueryRefresh';
import {ScheduleSwitch} from '../schedules/ScheduleSwitch';
import {humanCronString} from '../schedules/humanCronString';
import {ScheduleSwitchFragment} from '../schedules/types/ScheduleSwitchFragment.types';
import {SensorSwitch} from '../sensors/SensorSwitch';
import {SensorSwitchFragment} from '../sensors/types/SensorSwitchFragment.types';

interface JobRowProps {
  index: number;
  name: string;
  isJob: boolean;
  repoAddress: RepoAddress;
}

export const VirtualizedObserveJobRow = forwardRef(
  (props: JobRowProps, ref: React.ForwardedRef<HTMLDivElement>) => {
    const {index, name, isJob, repoAddress} = props;

    // Wait 100ms before querying in case we're scrolling the table really fast
    const shouldQuery = useDelayedState(100);
    const queryResult = useQuery<SingleJobQuery, SingleJobQueryVariables>(SINGLE_JOB_QUERY, {
      variables: {
        selector: buildPipelineSelector(repoAddress, name),
      },
      skip: !shouldQuery,
    });
    useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

    const {data} = queryResult;
    const pipeline =
      data?.pipelineOrError.__typename === 'Pipeline' ? data?.pipelineOrError : undefined;

    const {schedules, sensors} = useMemo(() => {
      if (pipeline) {
        const {schedules, sensors} = pipeline;
        return {schedules, sensors};
      }
      return {schedules: [], sensors: []};
    }, [pipeline]);

    const latestRuns = useMemo(() => {
      if (pipeline) {
        const {runs} = pipeline;
        if (runs.length) {
          return [...runs];
        }
      }
      return [];
    }, [pipeline]);

    const right = () => {
      if (queryResult.loading && !queryResult.data) {
        return <Skeleton $width={200} $height={24} />;
      }

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
                    <TimeFromNow unixTimestamp={latestRuns[0].startTime} showTooltip={false} />
                  </HoverButton>
                </Popover>
              ) : null,
            },
            {
              key: 'runs',
              control: (
                <Box padding={{horizontal: 8}}>
                  <RunStatusPezList
                    jobName={name}
                    runs={[...latestRuns].reverse()}
                    fade
                    forceCount={5}
                  />
                </Box>
              ),
            },
            {
              key: 'schedules',
              control:
                schedules.length > 0 ? (
                  <AutomationButton
                    type="schedule"
                    enabled={schedules.some(
                      (schedule) => schedule.scheduleState.status === 'RUNNING',
                    )}
                    automations={schedules}
                    repoAddress={repoAddress}
                  />
                ) : null,
            },
            {
              key: 'sensors',
              control:
                sensors.length > 0 ? (
                  <AutomationButton
                    type="sensor"
                    enabled={sensors.some((sensor) => sensor.sensorState.status === 'RUNNING')}
                    automations={sensors}
                    repoAddress={repoAddress}
                  />
                ) : null,
            },
            {
              key: 'automations',
              control:
                sensors.length === 0 && schedules.length === 0 ? (
                  <Tooltip content="No automations" placement="top">
                    <AutomationButton type="none" />
                  </Tooltip>
                ) : null,
            },
            {
              key: 'menu',
              control: (
                <JobMenu
                  job={{name, isJob, runs: latestRuns}}
                  isAssetJob={pipeline ? pipeline.isAssetJob : 'loading'}
                  repoAddress={repoAddress}
                />
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
        href={workspacePathFromAddress(repoAddress, `/jobs/${name}`)}
        renderLink={({href, ...props}) => <Link to={href || '#'} {...props} />}
        left={
          <Box flex={{direction: 'row', gap: 12, alignItems: 'center'}}>
            <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
              <Icon name="job" />
              {name}
            </Box>
            {pipeline?.description ? (
              <Tooltip
                content={<div style={{width: 320}}>{pipeline.description}</div>}
                placement="top"
              >
                <Icon name="info" color={Colors.textLight()} />
              </Tooltip>
            ) : null}
          </Box>
        }
        right={right()}
      />
    );
  },
);

type AutomationType = 'sensor' | 'schedule' | 'none';

interface AutomationButtonProps {
  type: AutomationType;
  enabled?: boolean;
  automations?: ScheduleSwitchFragment[] | SensorSwitchFragment[];
  repoAddress?: RepoAddress;
}

const AutomationButton = ({type, automations, enabled, repoAddress}: AutomationButtonProps) => {
  const icon = () => {
    if (type === 'none') {
      return <Icon name="status" color={Colors.accentGray()} />;
    }

    return <Icon name={type} color={enabled ? Colors.accentGreen() : Colors.accentGray()} />;
  };

  const button = (
    <HoverButton>
      <Box padding={{vertical: 2}}>{icon()}</Box>
    </HoverButton>
  );

  if (type === 'none') {
    return button;
  }

  const count = automations?.length || 0;
  const headerText =
    type === 'sensor'
      ? count === 1
        ? '1 sensor'
        : `${count} sensors`
      : count === 1
        ? '1 schedule'
        : `${count} schedules`;

  return (
    <Popover
      position="top"
      interactionKind="hover"
      content={
        <Box
          flex={{direction: 'column'}}
          style={{width: 320, overflowX: 'hidden'}}
          background={Colors.backgroundLighter()}
        >
          <Box
            flex={{direction: 'row', gap: 8, alignItems: 'center'}}
            padding={{vertical: 12, horizontal: 12}}
            border="bottom"
          >
            <strong style={{fontSize: 14}}>{headerText}</strong>
          </Box>
          <div style={{overflowY: 'auto', maxHeight: 240}}>
            {automations?.length && repoAddress ? (
              automations.map((automation, ii) => {
                const displayName =
                  automation.__typename === 'Sensor'
                    ? automation.name
                    : humanCronString(automation.cronSchedule, {
                        longTimezoneName: automation.executionTimezone || 'UTC',
                      });
                return (
                  <Box
                    key={automation.id + '-' + ii}
                    flex={{
                      direction: 'row',
                      gap: 12,
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                    padding={12}
                    border={ii === 0 ? null : 'top'}
                  >
                    <Box
                      flex={{direction: 'row', alignItems: 'center', gap: 8}}
                      style={{width: '100%', overflow: 'hidden'}}
                    >
                      <Icon name={automation.__typename === 'Schedule' ? 'schedule' : 'sensor'} />
                      <Link
                        to={workspacePathFromAddress(
                          repoAddress,
                          automation.__typename === 'Schedule'
                            ? `/schedules/${automation.name}`
                            : `/sensors/${automation.name}`,
                        )}
                        style={{flex: 1, overflow: 'hidden', width: '100%'}}
                      >
                        <MiddleTruncate text={displayName} />
                      </Link>
                    </Box>
                    <Box flex={{direction: 'row', alignItems: 'center', gap: 8}}>
                      {automation.__typename === 'Schedule' ? (
                        <ScheduleSwitch schedule={automation} repoAddress={repoAddress} />
                      ) : (
                        <SensorSwitch sensor={automation} repoAddress={repoAddress} />
                      )}
                    </Box>
                  </Box>
                );
              })
            ) : (
              <div>No automations</div>
            )}
          </div>
        </Box>
      }
      hoverOpenDelay={100}
    >
      {button}
    </Popover>
  );
};
