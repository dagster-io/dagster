import {gql, useQuery} from '@apollo/client';
import {Colors, NonIdealState, Tooltip} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {Link, Redirect, RouteComponentProps} from 'react-router-dom';
import styled from 'styled-components/macro';

import {Timestamp} from 'src/app/time/Timestamp';
import {PipelineGraph, PIPELINE_GRAPH_SOLID_FRAGMENT} from 'src/graph/PipelineGraph';
import {SVGViewport} from 'src/graph/SVGViewport';
import {getDagrePipelineLayout} from 'src/graph/getFullSolidLayout';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {explorerPathFromString} from 'src/pipelines/PipelinePathUtils';
import {OverviewJobFragment} from 'src/pipelines/types/OverviewJobFragment';
import {
  PipelineOverviewQuery,
  PipelineOverviewQueryVariables,
  PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs,
} from 'src/pipelines/types/PipelineOverviewQuery';
import {RunActionsMenu} from 'src/runs/RunActionsMenu';
import {RunStatus, RunStatusWithStats} from 'src/runs/RunStatusDots';
import {
  RunTime,
  RunsQueryRefetchContext,
  titleForRun,
  RunElapsed,
  RUN_ACTION_MENU_FRAGMENT,
  RUN_TIME_FRAGMENT,
} from 'src/runs/RunUtils';
import {JobType} from 'src/types/globalTypes';
import {Loading} from 'src/ui/Loading';
import {Table} from 'src/ui/Table';
import {FontFamily} from 'src/ui/styles';
import {repoAddressToSelector} from 'src/workspace/repoAddressToSelector';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';

type Run = PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs;

type Props = RouteComponentProps<{pipelinePath: string}> & {repoAddress: RepoAddress};

export const PipelineOverviewRoot: React.FC<Props> = (props) => {
  const {match, repoAddress} = props;
  const {pipelineName, snapshotId} = explorerPathFromString(match.params.pipelinePath);
  useDocumentTitle(`Pipeline: ${pipelineName}`);

  const repositorySelector = repoAddressToSelector(repoAddress);
  const pipelineSelector = {
    pipelineName,
    ...repositorySelector,
  };

  const queryResult = useQuery<PipelineOverviewQuery, PipelineOverviewQueryVariables>(
    PIPELINE_OVERVIEW_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      partialRefetch: true,
      variables: {pipelineSelector, limit: 5},
    },
  );

  if (snapshotId) {
    return (
      <Redirect to={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}/overview`)} />
    );
  }

  return (
    <Loading queryResult={queryResult}>
      {({pipelineSnapshotOrError}) => {
        if (pipelineSnapshotOrError.__typename === 'PipelineSnapshotNotFoundError') {
          return (
            <NonIdealState
              icon={IconNames.FLOW_BRANCH}
              title="Pipeline Snapshot Not Found"
              description={pipelineSnapshotOrError.message}
            />
          );
        }
        if (pipelineSnapshotOrError.__typename === 'PipelineNotFoundError') {
          return (
            <NonIdealState
              icon={IconNames.FLOW_BRANCH}
              title="Pipeline Not Found"
              description={pipelineSnapshotOrError.message}
            />
          );
        }
        if (pipelineSnapshotOrError.__typename === 'PythonError') {
          return (
            <NonIdealState
              icon={IconNames.ERROR}
              title="Query Error"
              description={pipelineSnapshotOrError.message}
            />
          );
        }

        const solids = pipelineSnapshotOrError.solidHandles.map((handle) => handle.solid);
        const schedules = pipelineSnapshotOrError.schedules;
        const sensors = pipelineSnapshotOrError.sensors;

        return (
          <RootContainer>
            <MainContainer>
              <OverviewSection title="Definition">
                <div
                  style={{
                    position: 'relative',
                    height: 550,
                    maxWidth: '40vw',
                    border: `1px solid ${Colors.LIGHT_GRAY1}`,
                    boxShadow: `0 1px 1px rgba(0, 0, 0, 0.2)`,
                  }}
                >
                  <PipelineGraph
                    pipelineName={pipelineName}
                    backgroundColor={Colors.LIGHT_GRAY5}
                    solids={solids}
                    layout={getDagrePipelineLayout(solids)}
                    interactor={SVGViewport.Interactors.None}
                    focusSolids={[]}
                    highlightedSolids={[]}
                  />
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'flex-end',
                      margin: '10px 0',
                    }}
                  >
                    <Link to={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}`)}>
                      Explore Pipeline Definition &gt;
                    </Link>
                  </div>
                </div>
              </OverviewSection>
              <OverviewSection title="Description">
                {pipelineSnapshotOrError.description || 'No description provided'}
              </OverviewSection>
            </MainContainer>
            <SecondaryContainer>
              <OverviewSection title="Schedule">
                {schedules.length ? (
                  <Table $compact>
                    <tbody>
                      {schedules.map((schedule) => (
                        <OverviewJob
                          repoAddress={repoAddress}
                          name={schedule.name}
                          key={schedule.name}
                          jobState={schedule.scheduleState}
                          jobType={JobType.SCHEDULE}
                          nextTick={schedule.futureTicks.results[0]}
                        />
                      ))}
                    </tbody>
                  </Table>
                ) : (
                  'No pipeline schedules'
                )}
              </OverviewSection>
              <OverviewSection title="Sensor">
                {sensors.length ? (
                  <Table $compact>
                    <tbody>
                      {sensors.map((sensor) => (
                        <OverviewJob
                          repoAddress={repoAddress}
                          name={sensor.name}
                          key={sensor.name}
                          jobState={sensor.sensorState}
                          jobType={JobType.SENSOR}
                          nextTick={sensor.nextTick || undefined}
                        />
                      ))}
                    </tbody>
                  </Table>
                ) : (
                  'No pipeline sensors'
                )}
              </OverviewSection>
              <RunsQueryRefetchContext.Provider value={{refetch: queryResult.refetch}}>
                <OverviewSection title="Recent runs">
                  {pipelineSnapshotOrError.runs.length ? (
                    <Table $compact>
                      <tbody>
                        {pipelineSnapshotOrError.runs.map((run) => (
                          <OverviewRun run={run} key={run.runId} />
                        ))}
                      </tbody>
                    </Table>
                  ) : (
                    'No recent runs'
                  )}
                </OverviewSection>
              </RunsQueryRefetchContext.Provider>
            </SecondaryContainer>
            <SecondaryContainer>
              <OverviewAssets runs={pipelineSnapshotOrError.runs} />
            </SecondaryContainer>
          </RootContainer>
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
    <OverviewSection title="Related assets">
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
    </OverviewSection>
  );
};

const OverviewJob = ({
  repoAddress,
  name,
  jobState,
  jobType,
  nextTick,
}: {
  repoAddress: RepoAddress;
  name: string;
  jobState: OverviewJobFragment;
  jobType: JobType;
  nextTick?: {
    timestamp: number;
  };
}) => {
  const lastRun = jobState.lastRuns.length && jobState.lastRuns[0];
  return (
    <tr>
      <td>
        <Link
          to={workspacePathFromAddress(
            repoAddress,
            `/${jobType === JobType.SCHEDULE ? 'schedules' : 'sensors'}/${name}`,
          )}
        >
          {name}
        </Link>
        {lastRun && lastRun.stats.__typename === 'PipelineRunStatsSnapshot' ? (
          <div style={{color: Colors.GRAY3, fontSize: 12, marginTop: 2}}>
            Last Run: <Timestamp unix={lastRun.stats.endTime || 0} />
          </div>
        ) : null}
        {nextTick ? (
          <div style={{color: Colors.GRAY3, fontSize: 12, marginTop: 2}}>
            Next Tick: <Timestamp unix={nextTick.timestamp || 0} />
          </div>
        ) : null}
        {jobState.runs && (
          <div style={{marginTop: '4px'}}>
            {jobState.runs.map((run) => {
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
      <td style={{width: '20px', textAlign: 'center'}}>
        <RunStatusWithStats status={run.status} runId={run.runId} />
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

const OverviewSection = ({title, children}: {title: string; children: any}) => {
  return (
    <div style={{marginBottom: 50}}>
      <div
        style={{
          textTransform: 'uppercase',
          color: Colors.GRAY2,
          marginBottom: 10,
        }}
      >
        {title}
      </div>
      {children}
    </div>
  );
};

const RootContainer = styled.div`
  flex: 1;
  display: flex;
  overflow: auto;
`;

const MainContainer = styled.div`
  flex: 2;
  max-width: 1200px;
  padding: 20px;
`;

const SecondaryContainer = ({children}: {children: React.ReactNode}) => (
  <div style={{maxWidth: 600, padding: 20, flex: 1}}>
    <div style={{maxWidth: '25vw'}}>{children}</div>
  </div>
);

const OVERVIEW_JOB_FRAGMENT = gql`
  fragment OverviewJobFragment on JobState {
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

const PIPELINE_OVERVIEW_QUERY = gql`
  query PipelineOverviewQuery($pipelineSelector: PipelineSelector!, $limit: Int!) {
    pipelineSnapshotOrError(activePipelineSelector: $pipelineSelector) {
      ... on PipelineSnapshot {
        id
        name
        description
        solidHandles(parentHandleID: "") {
          solid {
            name
            ...PipelineGraphSolidFragment
          }
        }
        runs(limit: $limit) {
          ...RunActionMenuFragment
          ...RunTimeFragment
          id
          assets {
            key {
              path
            }
          }
        }
        schedules {
          id
          name
          scheduleState {
            id
            ...OverviewJobFragment
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
          sensorState {
            id
            ...OverviewJobFragment
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
  ${PIPELINE_GRAPH_SOLID_FRAGMENT}
  ${OVERVIEW_JOB_FRAGMENT}
  ${RUN_TIME_FRAGMENT}
  ${RUN_ACTION_MENU_FRAGMENT}
`;
