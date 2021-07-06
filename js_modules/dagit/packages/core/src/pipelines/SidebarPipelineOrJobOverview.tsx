import {gql, useQuery} from '@apollo/client';
import {Colors, Tooltip} from '@blueprintjs/core';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {Timestamp} from '../app/time/Timestamp';
import {RunActionsMenu} from '../runs/RunActionsMenu';
import {RunStatus, RunStatusWithStats} from '../runs/RunStatusDots';
import {
  RunElapsed,
  RunsQueryRefetchContext,
  RunTime,
  RUN_ACTION_MENU_FRAGMENT,
  RUN_TIME_FRAGMENT,
  titleForRun,
} from '../runs/RunUtils';
import {InstigationType} from '../types/globalTypes';
import {Loading} from '../ui/Loading';
import {Table} from '../ui/Table';
import {FontFamily} from '../ui/styles';
import {usePipelineSelector} from '../workspace/WorkspaceContext';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {NonIdealPipelineQueryResult} from './NonIdealPipelineQueryResult';
import {PipelineExplorerPath} from './PipelinePathUtils';
import {SidebarSection} from './SidebarComponents';
import {SidebarModeSection, SIDEBAR_MODE_INFO_FRAGMENT} from './SidebarModeSection';
import {
  JobOverviewSidebarQuery,
  JobOverviewSidebarQueryVariables,
  JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs,
} from './types/JobOverviewSidebarQuery';
import {OverviewInstigationFragment} from './types/OverviewInstigationFragment';

type Run = JobOverviewSidebarQuery_pipelineSnapshotOrError_PipelineSnapshot_runs;

export const SidebarPipelineOrJobOverview: React.FC<{
  repoAddress: RepoAddress;
  explorerPath: PipelineExplorerPath;
}> = (props) => {
  const {flagPipelineModeTuples} = useFeatureFlags();
  const pipelineSelector = usePipelineSelector(props.repoAddress, props.explorerPath.pipelineName);

  const queryResult = useQuery<JobOverviewSidebarQuery, JobOverviewSidebarQueryVariables>(
    JOB_OVERVIEW_SIDEBAR_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      partialRefetch: true,
      variables: {pipelineSelector: pipelineSelector, limit: 5},
    },
  );

  return (
    <Loading queryResult={queryResult}>
      {({pipelineSnapshotOrError}) => {
        if (pipelineSnapshotOrError.__typename !== 'PipelineSnapshot') {
          return <NonIdealPipelineQueryResult result={pipelineSnapshotOrError} />;
        }

        let schedules = pipelineSnapshotOrError.schedules;
        let sensors = pipelineSnapshotOrError.sensors;
        let modes = pipelineSnapshotOrError.modes;

        if (flagPipelineModeTuples) {
          schedules = schedules.filter((m) => m.mode === props.explorerPath.pipelineMode);
          sensors = sensors.filter((m) => m.mode === props.explorerPath.pipelineMode);
          modes = modes.filter((m) => m.name === props.explorerPath.pipelineMode);
        }

        return (
          <div>
            <SidebarSection title={'Description'}>
              {pipelineSnapshotOrError.description || 'No description provided'}
            </SidebarSection>
            <SidebarSection title={'Resources'}>
              {modes.map((mode) => (
                <SidebarModeSection mode={mode} key={mode.name} />
              ))}
            </SidebarSection>
            <SidebarSection title={'Schedule'}>
              {schedules.length ? (
                <Table $compact>
                  <tbody>
                    {schedules.map((schedule) => (
                      <OverviewInstigation
                        repoAddress={props.repoAddress}
                        name={schedule.name}
                        key={schedule.name}
                        instigationState={schedule.scheduleState}
                        instigationType={InstigationType.SCHEDULE}
                        nextTick={schedule.futureTicks.results[0]}
                      />
                    ))}
                  </tbody>
                </Table>
              ) : flagPipelineModeTuples ? (
                'No job schedules'
              ) : (
                'No pipeline schedules'
              )}
            </SidebarSection>
            <SidebarSection title={'Sensor'}>
              {sensors.length ? (
                <Table $compact>
                  <tbody>
                    {sensors.map((sensor) => (
                      <OverviewInstigation
                        repoAddress={props.repoAddress}
                        name={sensor.name}
                        key={sensor.name}
                        instigationState={sensor.sensorState}
                        instigationType={InstigationType.SENSOR}
                        nextTick={sensor.nextTick || undefined}
                      />
                    ))}
                  </tbody>
                </Table>
              ) : flagPipelineModeTuples ? (
                'No job sensors'
              ) : (
                'No pipeline sensors'
              )}
            </SidebarSection>

            <RunsQueryRefetchContext.Provider value={{refetch: queryResult.refetch}}>
              <SidebarSection title={'Recent Runs'}>
                {pipelineSnapshotOrError.runs.length ? (
                  <div>
                    {pipelineSnapshotOrError.runs.map((run) => (
                      <OverviewRun run={run} key={run.runId} />
                    ))}
                  </div>
                ) : (
                  'No recent runs'
                )}
              </SidebarSection>
            </RunsQueryRefetchContext.Provider>

            <SidebarSection title={'Related Assets'}>
              <OverviewAssets runs={pipelineSnapshotOrError.runs} />
            </SidebarSection>
          </div>
        );
      }}
    </Loading>
  );
};

const OverviewAssets = ({runs}: {runs: Run[]}) => {
  const assetMap = {};
  runs.forEach((run) => {
    run.assets.forEach((asset) => {
      const assetKeyStr = asset.key.path.join('/');
      assetMap[assetKeyStr] = true;
    });
  });
  const assetKeys = Object.keys(assetMap);
  return (
    <>
      {assetKeys.length ? (
        <Table>
          <tbody>
            {assetKeys.map((assetKey) => (
              <tr key={assetKey} style={{padding: 10, paddingBottom: 30}}>
                <td>
                  <Link to={`/instance/assets/${assetKey}`}>{assetKey}</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      ) : (
        'No recent assets'
      )}
    </>
  );
};

const OverviewInstigation = ({
  repoAddress,
  name,
  instigationState,
  instigationType,
  nextTick,
}: {
  repoAddress: RepoAddress;
  name: string;
  instigationState: OverviewInstigationFragment;
  instigationType: InstigationType;
  nextTick?: {
    timestamp: number;
  };
}) => {
  const lastRun = instigationState.lastRuns.length && instigationState.lastRuns[0];
  return (
    <tr>
      <td>
        <Link
          to={workspacePathFromAddress(
            repoAddress,
            `/${instigationType === InstigationType.SCHEDULE ? 'schedules' : 'sensors'}/${name}`,
          )}
        >
          {name}
        </Link>
        {lastRun && lastRun.stats.__typename === 'PipelineRunStatsSnapshot' ? (
          <div style={{color: Colors.GRAY3, fontSize: 12, marginTop: 2}}>
            Last Run: <Timestamp timestamp={{unix: lastRun.stats.endTime || 0}} />
          </div>
        ) : null}
        {nextTick ? (
          <div style={{color: Colors.GRAY3, fontSize: 12, marginTop: 2}}>
            Next Tick: <Timestamp timestamp={{unix: nextTick.timestamp || 0}} />
          </div>
        ) : null}
        {instigationState.runs && (
          <div style={{marginTop: '4px'}}>
            {instigationState.runs.map((run) => {
              return (
                <div
                  style={{
                    display: 'inline-block',
                    cursor: 'pointer',
                    marginRight: 5,
                  }}
                  key={run.runId}
                >
                  <Link to={`/instance/runs/${run.runId}`}>
                    <Tooltip
                      position={'top'}
                      content={titleForRun(run)}
                      wrapperTagName="div"
                      targetTagName="div"
                    >
                      <RunStatus status={run.status} />
                    </Tooltip>
                  </Link>
                </div>
              );
            })}
          </div>
        )}
      </td>
    </tr>
  );
};

const OverviewRun = ({run}: {run: Run}) => {
  const time = run.stats.__typename === 'PipelineRunStatsSnapshot' ? <RunTime run={run} /> : null;
  const elapsed =
    run.stats.__typename === 'PipelineRunStatsSnapshot' ? <RunElapsed run={run} /> : null;

  return (
    <tr>
      <td style={{width: '20px'}}>
        <div style={{paddingTop: '1px'}}>
          <RunStatusWithStats status={run.status} runId={run.runId} />
        </div>
      </td>
      <td style={{width: '100%'}}>
        <div style={{fontFamily: FontFamily.monospace}}>
          <Link to={`/instance/runs/${run.runId}`}>{titleForRun(run)}</Link>
        </div>
        <div style={{marginTop: 5}}>{`Mode: ${run.mode}`}</div>
        {time}
        {elapsed}
      </td>
      <td style={{width: '50px'}}>
        <RunActionsMenu run={run} />
      </td>
    </tr>
  );
};

const OVERVIEW_INSTIGATION_FRAGMENT = gql`
  fragment OverviewInstigationFragment on InstigationState {
    id
    runsCount
    lastRuns: runs(limit: 1) {
      id
      stats {
        ... on PipelineRunStatsSnapshot {
          id
          endTime
        }
      }
    }
    runs(limit: 10) {
      id
      runId
      pipelineName
      status
    }
    status
  }
`;

const JOB_OVERVIEW_SIDEBAR_QUERY = gql`
  query JobOverviewSidebarQuery($pipelineSelector: PipelineSelector!, $limit: Int!) {
    pipelineSnapshotOrError(activePipelineSelector: $pipelineSelector) {
      ... on PipelineSnapshot {
        id
        name
        description

        modes {
          id
          ...SidebarModeInfoFragment
        }
        runs(limit: $limit) {
          ...RunActionMenuFragment
          ...RunTimeFragment
          id
          assets {
            id
            key {
              path
            }
          }
        }
        schedules {
          id
          name
          mode
          scheduleState {
            id
            ...OverviewInstigationFragment
          }
          futureTicks(limit: 1) {
            results {
              timestamp
            }
          }
        }
        sensors {
          id
          name
          mode
          sensorState {
            id
            ...OverviewInstigationFragment
          }
          nextTick {
            timestamp
          }
        }
      }
      ... on PipelineNotFoundError {
        message
      }
      ... on PipelineSnapshotNotFoundError {
        message
      }
      ... on PythonError {
        message
      }
    }
  }
  ${OVERVIEW_INSTIGATION_FRAGMENT}
  ${SIDEBAR_MODE_INFO_FRAGMENT}
  ${RUN_TIME_FRAGMENT}
  ${RUN_ACTION_MENU_FRAGMENT}
`;
