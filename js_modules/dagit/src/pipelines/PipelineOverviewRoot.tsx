import {Colors, NonIdealState, Tooltip} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import gql from 'graphql-tag';
import * as React from 'react';
import {useQuery} from 'react-apollo';
import {Link, Redirect} from 'react-router-dom';
import {RouteComponentProps} from 'react-router-dom';
import styled from 'styled-components/macro';

import {usePipelineSelector} from 'src/DagsterRepositoryContext';
import {RowColumn, RowContainer} from 'src/ListComponents';
import {Loading} from 'src/Loading';
import {explorerPathFromString} from 'src/PipelinePathUtils';
import {Timestamp} from 'src/TimeComponents';
import {PipelineGraph} from 'src/graph/PipelineGraph';
import {SVGViewport} from 'src/graph/SVGViewport';
import {getDagrePipelineLayout} from 'src/graph/getFullSolidLayout';
import {useDocumentTitle} from 'src/hooks/useDocumentTitle';
import {
  PipelineOverviewQuery,
  PipelineOverviewQueryVariables,
  PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs,
  PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules,
} from 'src/pipelines/types/PipelineOverviewQuery';
import {RunActionsMenu} from 'src/runs/RunActionsMenu';
import {RunStatus, RunStatusWithStats} from 'src/runs/RunStatusDots';
import {RunTime, RunsQueryRefetchContext, titleForRun} from 'src/runs/RunUtils';
import {RunComponentFragments, RunElapsed} from 'src/runs/RunUtils';

type Run = PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs;
type Schedule = PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_schedules;

export const PipelineOverviewRoot: React.FunctionComponent<RouteComponentProps<{
  pipelinePath: string;
}>> = ({match}) => {
  const {pipelineName, snapshotId} = explorerPathFromString(match.params.pipelinePath);
  useDocumentTitle(`Pipeline: ${pipelineName}`);

  const pipelineSelector = usePipelineSelector(pipelineName);
  const queryResult = useQuery<PipelineOverviewQuery, PipelineOverviewQueryVariables>(
    PIPELINE_OVERVIEW_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      partialRefetch: true,
      variables: {pipelineSelector, limit: 5},
    },
  );

  if (snapshotId) {
    return <Redirect to={`/pipeline/${pipelineName}/overview`} />;
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
                    <Link to={`/pipeline/${pipelineName}:`}>Explore Pipeline Definition &gt;</Link>
                  </div>
                </div>
              </OverviewSection>
              <OverviewSection title="Description">
                {pipelineSnapshotOrError.description || 'No description provided'}
              </OverviewSection>
            </MainContainer>
            <SecondaryContainer>
              <OverviewSection title="Schedule">
                {schedules.length
                  ? schedules.map((schedule) => (
                      <OverviewSchedule schedule={schedule} key={schedule.name} />
                    ))
                  : 'No pipeline schedules'}
              </OverviewSection>
              <RunsQueryRefetchContext.Provider value={{refetch: queryResult.refetch}}>
                <OverviewSection title="Recent runs">
                  {pipelineSnapshotOrError.runs.length
                    ? pipelineSnapshotOrError.runs.map((run) => (
                        <OverviewRun run={run} key={run.runId} />
                      ))
                    : 'No recent runs'}
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
      {assetKeys.length
        ? assetKeys.map((assetKey) => (
            <RowContainer key={assetKey} style={{padding: 10, paddingBottom: 30}}>
              <Link to={`/assets/${assetKey}`}>{assetKey}</Link>
            </RowContainer>
          ))
        : 'No recent assets'}
    </OverviewSection>
  );
};

const OverviewSchedule = ({schedule}: {schedule: Schedule}) => {
  const lastRun =
    schedule.scheduleState &&
    schedule.scheduleState.lastRuns.length &&
    schedule.scheduleState.lastRuns[0];
  return (
    <RowContainer style={{paddingRight: 3}}>
      <RowColumn>
        <Link to={`/schedules/${schedule.name}`}>{schedule.name}</Link>
        {lastRun && lastRun.stats.__typename === 'PipelineRunStatsSnapshot' ? (
          <div style={{color: Colors.GRAY3, fontSize: 12, marginTop: 2}}>
            Last Run: <Timestamp unix={lastRun.stats.endTime || 0} />
          </div>
        ) : null}
        <div style={{marginTop: 5}}>
          {schedule.scheduleState &&
            schedule.scheduleState.runs.map((run) => {
              return (
                <div
                  style={{
                    display: 'inline-block',
                    cursor: 'pointer',
                    marginRight: 5,
                  }}
                  key={run.runId}
                >
                  <Link to={`/pipeline/${run.pipelineName}/runs/${run.runId}`}>
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
      </RowColumn>
    </RowContainer>
  );
};

const OverviewRun = ({run}: {run: Run}) => {
  const time = run.stats.__typename === 'PipelineRunStatsSnapshot' ? <RunTime run={run} /> : null;
  const elapsed =
    run.stats.__typename === 'PipelineRunStatsSnapshot' ? <RunElapsed run={run} /> : null;

  return (
    <RowContainer style={{paddingRight: 3}}>
      <RowColumn style={{maxWidth: 30, paddingLeft: 0, textAlign: 'center'}}>
        <RunStatusWithStats status={run.status} runId={run.runId} />
      </RowColumn>
      <RowColumn style={{flex: 2.4}}>
        <Link to={`/pipeline/${run.pipelineName}/runs/${run.runId}`}>{titleForRun(run)}</Link>
        <div style={{marginTop: 5}}>{`Mode: ${run.mode}`}</div>
        {time}
        {elapsed}
      </RowColumn>
      <RowColumn style={{maxWidth: 50}}>
        <RunActionsMenu run={run} />
      </RowColumn>
    </RowContainer>
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

const OverviewScheduleFragment = gql`
  fragment OverviewScheduleFragment on ScheduleDefinition {
    __typename
    name
    scheduleState {
      runsCount
      lastRuns: runs(limit: 1) {
        stats {
          ... on PipelineRunStatsSnapshot {
            endTime
          }
        }
      }
      runs(limit: 10) {
        runId
        pipelineName
        status
      }
      status
    }
  }
`;

export const PIPELINE_OVERVIEW_QUERY = gql`
  query PipelineOverviewQuery($pipelineSelector: PipelineSelector!, $limit: Int!) {
    pipelineSnapshotOrError(activePipelineSelector: $pipelineSelector) {
      ... on PipelineSnapshot {
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
          assets {
            key {
              path
            }
          }
        }
        schedules {
          ...OverviewScheduleFragment
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
  ${PipelineGraph.fragments.PipelineGraphSolidFragment}
  ${OverviewScheduleFragment}
  ${RunComponentFragments.RUN_TIME_FRAGMENT}
  ${RunComponentFragments.RUN_ACTION_MENU_FRAGMENT}
`;
