import {gql, useQuery} from '@apollo/client';
import {Colors, NonIdealState, Tooltip} from '@blueprintjs/core';
import {IconNames} from '@blueprintjs/icons';
import * as React from 'react';
import {Link, RouteComponentProps} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {Timestamp} from '../app/time/Timestamp';
import {PipelineGraph, PIPELINE_GRAPH_SOLID_FRAGMENT} from '../graph/PipelineGraph';
import {SVGViewport} from '../graph/SVGViewport';
import {getDagrePipelineLayout} from '../graph/getFullSolidLayout';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {RunActionsMenu} from '../runs/RunActionsMenu';
import {RunStatus, RunStatusWithStats} from '../runs/RunStatusDots';
import {
  RunTime,
  RunsQueryRefetchContext,
  titleForRun,
  RunElapsed,
  RUN_ACTION_MENU_FRAGMENT,
  RUN_TIME_FRAGMENT,
} from '../runs/RunUtils';
import {JobType} from '../types/globalTypes';
import {Box} from '../ui/Box';
import {Loading} from '../ui/Loading';
import {Table} from '../ui/Table';
import {FontFamily} from '../ui/styles';
import {repoAddressToSelector} from '../workspace/repoAddressToSelector';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {explorerPathFromString, useStripSnapshotFromPath} from './PipelinePathUtils';
import {OverviewJobFragment} from './types/OverviewJobFragment';
import {
  PipelineOverviewQuery,
  PipelineOverviewQueryVariables,
  PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs,
} from './types/PipelineOverviewQuery';

type Run = PipelineOverviewQuery_pipelineSnapshotOrError_PipelineSnapshot_runs;

type Props = RouteComponentProps<{pipelinePath: string}> & {repoAddress: RepoAddress};

export const PipelineOverviewRoot: React.FC<Props> = (props) => {
  const {match, repoAddress} = props;
  const {pipelineName} = explorerPathFromString(match.params.pipelinePath);
  useDocumentTitle(`Pipeline: ${pipelineName}`);
  useStripSnapshotFromPath(props.match.params);
  const {flagPipelineModeTuples} = useFeatureFlags();

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
          <Box flex={{direction: 'row'}} padding={20}>
            <Box style={{flexBasis: '50%'}} margin={{right: 32}}>
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
                    {flagPipelineModeTuples ? (
                      <Link to={workspacePathFromAddress(repoAddress, `/graphs/${pipelineName}`)}>
                        Explore graph definition &#187;
                      </Link>
                    ) : (
                      <Link
                        to={workspacePathFromAddress(repoAddress, `/pipelines/${pipelineName}`)}
                      >
                        Explore pipeline definition &#187;
                      </Link>
                    )}
                  </div>
                </div>
              </OverviewSection>
              <OverviewSection title="Description">
                {pipelineSnapshotOrError.description || 'No description provided'}
              </OverviewSection>
            </Box>
            <Box style={{flexBasis: '25%'}} margin={{right: 32}}>
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
                ) : flagPipelineModeTuples ? (
                  'No job schedules'
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
                ) : flagPipelineModeTuples ? (
                  'No job sensors'
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
            </Box>
            <div style={{flexBasis: '25%'}}>
              <OverviewAssets runs={pipelineSnapshotOrError.runs} />
            </div>
          </Box>
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
            Last Run: <Timestamp timestamp={{unix: lastRun.stats.endTime || 0}} />
          </div>
        ) : null}
        {nextTick ? (
          <div style={{color: Colors.GRAY3, fontSize: 12, marginTop: 2}}>
            Next Tick: <Timestamp timestamp={{unix: nextTick.timestamp || 0}} />
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
            id
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
