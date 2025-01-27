import {
  Box,
  Button,
  Colors,
  ErrorBoundary,
  Icon,
  NonIdealState,
  SplitPanelContainer,
  SplitPanelContainerHandle,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {memo, useLayoutEffect, useMemo, useRef, useState} from 'react';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';
import styled from 'styled-components';

import {CapturedOrExternalLogPanel} from './CapturedLogPanel';
import {LogFilter, LogsProvider, LogsProviderLogs} from './LogsProvider';
import {LogsScrollingTable} from './LogsScrollingTable';
import {LogType, LogsToolbar} from './LogsToolbar';
import {RunActionButtons} from './RunActionButtons';
import {RunContext} from './RunContext';
import {IRunMetadataDict, RunMetadataProvider} from './RunMetadataProvider';
import {RunDagsterRunEventFragment, RunPageFragment} from './types/RunFragments.types';
import {
  matchingComputeLogKeyFromStepKey,
  useComputeLogFileKeyForSelection,
} from './useComputeLogFileKeyForSelection';
import {useQueryPersistedLogFilter} from './useQueryPersistedLogFilter';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {featureEnabled} from '../app/Flags';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {GanttChart, GanttChartLoadingState, GanttChartMode, QueuedState} from '../gantt/GanttChart';
import {toGraphQueryItems} from '../gantt/toGraphQueryItems';
import {RunStatus} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useFavicon} from '../hooks/useFavicon';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {CompletionType, useTraceDependency} from '../performance/TraceContext';
import {filterRunSelectionByQuery} from '../run-selection/AntlrRunSelection';

interface RunProps {
  runId: string;
  run?: RunPageFragment;
}

const runStatusFavicon = (status: RunStatus) => {
  switch (status) {
    case RunStatus.FAILURE:
      return '/favicon-run-failed.svg';
    case RunStatus.SUCCESS:
      return '/favicon-run-success.svg';
    case RunStatus.STARTING:
    case RunStatus.STARTED:
    case RunStatus.CANCELING:
      return '/favicon-run-pending.svg';
    default:
      return '/favicon.svg';
  }
};

export const Run = memo((props: RunProps) => {
  const {run, runId} = props;
  const [logsFilter, setLogsFilter] = useQueryPersistedLogFilter();
  const [selectionQuery, setSelectionQuery] = useQueryPersistedState<string>({
    queryKey: 'selection',
    defaults: {selection: ''},
  });

  useFavicon(run ? runStatusFavicon(run.status) : '/favicon.svg');
  useDocumentTitle(
    run
      ? `${!isHiddenAssetGroupJob(run.pipelineName) ? run.pipelineName : ''} ${runId.slice(
          0,
          8,
        )} [${run.status}]`
      : `Run: ${runId}`,
  );

  const onShowStateDetails = (stepKey: string, logs: RunDagsterRunEventFragment[]) => {
    const errorNode = logs.find(
      (node) => node.__typename === 'ExecutionStepFailureEvent' && node.stepKey === stepKey,
    );

    if (errorNode) {
      showCustomAlert({
        body: <PythonErrorInfo error={errorNode} />,
      });
    }
  };

  const onSetSelectionQuery = (query: string) => {
    setSelectionQuery(query);
    setLogsFilter({
      ...logsFilter,
      logQuery: query !== '*' ? [{token: 'query', value: query}] : [],
    });
  };

  const logsDependency = useTraceDependency('RunLogs');

  return (
    <RunContext.Provider value={run}>
      <LogsProvider key={runId} runId={runId}>
        {(logs) => (
          <>
            <OnLogsLoaded dependency={logsDependency} logs={logs} />
            <RunMetadataProvider logs={logs}>
              {(metadata) => (
                <RunWithData
                  run={run}
                  runId={runId}
                  logs={logs}
                  logsFilter={logsFilter}
                  metadata={metadata}
                  selectionQuery={selectionQuery}
                  onSetLogsFilter={setLogsFilter}
                  onSetSelectionQuery={onSetSelectionQuery}
                  onShowStateDetails={onShowStateDetails}
                />
              )}
            </RunMetadataProvider>
          </>
        )}
      </LogsProvider>
    </RunContext.Provider>
  );
});

const OnLogsLoaded = ({
  dependency,
  logs,
}: {
  dependency: ReturnType<typeof useTraceDependency>;
  logs: LogsProviderLogs;
}) => {
  useLayoutEffect(() => {
    if (!logs.loading) {
      dependency.completeDependency(CompletionType.SUCCESS);
    }
  }, [dependency, logs]);
  return null;
};

interface RunWithDataProps {
  run?: RunPageFragment;
  runId: string;
  selectionQuery: string;
  logs: LogsProviderLogs;
  logsFilter: LogFilter;
  metadata: IRunMetadataDict;
  onSetLogsFilter: (v: LogFilter) => void;
  onSetSelectionQuery: (query: string) => void;
  onShowStateDetails: (stepKey: string, logs: RunDagsterRunEventFragment[]) => void;
}

const logTypeFromQuery = (queryLogType: string) => {
  switch (queryLogType) {
    case 'stdout':
      return LogType.stdout;
    case 'stderr':
      return LogType.stderr;
    default:
      return LogType.structured;
  }
};

/**
 * Note: There are two places we keep a "step query string" in the Run view:
 * selectionQuery and logsFilter.logsQuery.
 *
 * - selectionQuery is set when you click around in the Gannt view and is the
 *   selection used for re-execution, etc. When set, we autofill logsFilter.logsQuery.
 *
 * - logsFilter.logsQuery is used for filtering the logs. It can be cleared separately
 *   from the selectionQuery, so you can select a step but navigate elsewhere in the logs.
 *
 * We could revisit this in the future but I believe we iterated quite a bit to get to this
 * solution and we should avoid locking the two filter inputs together completely.
 */
const RunWithData = ({
  run,
  runId,
  logs,
  logsFilter,
  metadata,
  selectionQuery,
  onSetLogsFilter,
  onSetSelectionQuery,
}: RunWithDataProps) => {
  const newRunSelectionSyntax = featureEnabled(FeatureFlag.flagSelectionSyntax);

  const [queryLogType, setQueryLogType] = useQueryPersistedState<string>({
    queryKey: 'logType',
    defaults: {logType: LogType.structured},
  });

  const logType = logTypeFromQuery(queryLogType);
  const setLogType = (lt: LogType) => setQueryLogType(LogType[lt]);
  const [computeLogUrl, setComputeLogUrl] = useState<string | null>(null);

  const stepKeysJSON = JSON.stringify(Object.keys(metadata.steps).sort());
  const stepKeys = useMemo(() => JSON.parse(stepKeysJSON), [stepKeysJSON]);

  const runtimeGraph = run?.executionPlan && toGraphQueryItems(run?.executionPlan, metadata.steps);

  const selectionStepKeys = useMemo(() => {
    return runtimeGraph && selectionQuery && selectionQuery !== '*'
      ? filterRunSelectionByQuery(runtimeGraph, selectionQuery).all.map((n) => n.name)
      : [];
  }, [runtimeGraph, selectionQuery]);

  const selection = useMemo(
    () => ({
      query: selectionQuery,
      keys: selectionStepKeys,
    }),
    [selectionStepKeys, selectionQuery],
  );

  const {logCaptureInfo, computeLogFileKey, setComputeLogFileKey} =
    useComputeLogFileKeyForSelection({
      stepKeys,
      selectionStepKeys,
      metadata,
      defaultToFirstStep: false,
    });

  const logsFilterStepKeys = useMemo(
    () =>
      runtimeGraph
        ? logsFilter.logQuery
            .filter((v) => v.token && v.token === 'query')
            .reduce((accum, v) => {
              accum.push(
                ...filterRunSelectionByQuery(runtimeGraph, v.value).all.map((n) => n.name),
              );
              return accum;
            }, [] as string[])
        : [],
    [logsFilter.logQuery, runtimeGraph],
  );

  const onClickStep = (stepKey: string, evt: React.MouseEvent<any>) => {
    const index = selectionStepKeys.indexOf(stepKey);
    let newSelected: string[] = [];
    const filterForExactStep = `"${stepKey}"`;
    let nextSelectionQuery = selectionQuery;
    if (evt.shiftKey) {
      // shift-click to multi select steps, preserving quotations if present
      newSelected = [
        ...selectionStepKeys.map((k) => (selectionQuery.includes(`"${k}"`) ? `"${k}"` : k)),
      ];

      if (index !== -1) {
        // deselect the step if already selected
        if (newRunSelectionSyntax) {
          nextSelectionQuery = removeStepFromSelection(nextSelectionQuery, stepKey);
        } else {
          newSelected.splice(index, 1);
        }
      } else {
        // select the step otherwise
        if (newRunSelectionSyntax) {
          nextSelectionQuery = addStepToSelection(nextSelectionQuery, stepKey);
        } else {
          newSelected.push(filterForExactStep);
        }
      }
    } else {
      // deselect the step if already selected
      if (selectionStepKeys.length === 1 && index !== -1) {
        if (newRunSelectionSyntax) {
          nextSelectionQuery = '';
        } else {
          newSelected = [];
        }
      } else {
        // select the step otherwise
        if (newRunSelectionSyntax) {
          nextSelectionQuery = `name:"${stepKey}"`;
        } else {
          newSelected = [filterForExactStep];
        }

        // When only one step is selected, set the compute log key as well.
        const matchingLogKey = matchingComputeLogKeyFromStepKey(metadata.logCaptureSteps, stepKey);
        if (matchingLogKey) {
          setComputeLogFileKey(matchingLogKey);
        }
      }
    }

    if (newRunSelectionSyntax) {
      onSetSelectionQuery(nextSelectionQuery);
    } else {
      onSetSelectionQuery(newSelected.join(', ') || '*');
    }
  };

  const [expandedPanel, setExpandedPanel] = useState<null | 'top' | 'bottom'>(null);
  const containerRef = useRef<SplitPanelContainerHandle>(null);

  useLayoutEffect(() => {
    if (containerRef.current) {
      const size = containerRef.current.getSize();
      if (size === 100) {
        setExpandedPanel('top');
      } else if (size === 0) {
        setExpandedPanel('bottom');
      }
    }
  }, []);

  const isTopExpanded = expandedPanel === 'top';
  const isBottomExpanded = expandedPanel === 'bottom';

  const expandBottomPanel = () => {
    containerRef.current?.changeSize(0);
    setExpandedPanel('bottom');
  };
  const expandTopPanel = () => {
    containerRef.current?.changeSize(100);
    setExpandedPanel('top');
  };
  const resetPanels = () => {
    containerRef.current?.changeSize(50);
    setExpandedPanel(null);
  };

  const gantt = (metadata: IRunMetadataDict) => {
    if (!run) {
      return <GanttChartLoadingState runId={runId} />;
    }

    if (run.status === 'QUEUED') {
      return <QueuedState run={run} />;
    }

    if (run.executionPlan && runtimeGraph) {
      return (
        <ErrorBoundary region="gantt chart">
          <GanttChart
            options={{
              mode: GanttChartMode.WATERFALL_TIMED,
            }}
            toolbarActions={
              <Box flex={{direction: 'row', alignItems: 'center', gap: 12}}>
                <Tooltip content={isTopExpanded ? 'Collapse' : 'Expand'}>
                  <Button
                    icon={<Icon name={isTopExpanded ? 'collapse_arrows' : 'expand_arrows'} />}
                    onClick={isTopExpanded ? resetPanels : expandTopPanel}
                  />
                </Tooltip>
                <RunActionButtons
                  run={run}
                  graph={runtimeGraph}
                  metadata={metadata}
                  selection={selection}
                />
              </Box>
            }
            runId={runId}
            graph={runtimeGraph}
            metadata={metadata}
            selection={selection}
            onClickStep={onClickStep}
            onSetSelection={onSetSelectionQuery}
            focusedTime={logsFilter.focusedTime}
          />
        </ErrorBoundary>
      );
    }

    return <NonIdealState icon="error" title="Unable to build execution plan" />;
  };

  return (
    <>
      <SplitPanelContainer
        ref={containerRef}
        axis="vertical"
        identifier="run-gantt"
        firstInitialPercent={35}
        firstMinSize={56}
        first={gantt(metadata)}
        secondMinSize={56}
        second={
          <ErrorBoundary region="logs">
            <LogsContainer>
              <LogsToolbar
                logType={logType}
                onSetLogType={setLogType}
                filter={logsFilter}
                onSetFilter={onSetLogsFilter}
                steps={stepKeys}
                metadata={metadata}
                computeLogFileKey={computeLogFileKey}
                onSetComputeLogKey={setComputeLogFileKey}
                computeLogUrl={computeLogUrl}
                counts={logs.counts}
                isSectionExpanded={isBottomExpanded}
                toggleExpanded={isBottomExpanded ? resetPanels : expandBottomPanel}
              />
              {logType !== LogType.structured ? (
                !computeLogFileKey ? (
                  <NoStepSelectionState type={logType} />
                ) : (
                  <CapturedOrExternalLogPanel
                    logKey={computeLogFileKey ? [runId, 'compute_logs', computeLogFileKey] : []}
                    logCaptureInfo={logCaptureInfo}
                    visibleIOType={LogType[logType]}
                    onSetDownloadUrl={setComputeLogUrl}
                  />
                )
              ) : (
                <LogsScrollingTable
                  logs={logs}
                  filter={logsFilter}
                  filterStepKeys={logsFilterStepKeys}
                  filterKey={`${JSON.stringify(logsFilter)}`}
                  metadata={metadata}
                />
              )}
            </LogsContainer>
          </ErrorBoundary>
        }
      />
    </>
  );
};

const LogsContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100%;
`;

const NoStepSelectionState = ({type}: {type: LogType}) => {
  return (
    <Box
      flex={{
        direction: 'row',
        grow: 1,
        alignItems: 'center',
        justifyContent: 'center',
      }}
      style={{background: Colors.backgroundDefault()}}
    >
      <NonIdealState
        title={`Select a step to view ${type}`}
        icon="warning"
        description="Select a step on the Gantt chart or from the dropdown above to view logs."
      />
    </Box>
  );
};

function removeStepFromSelection(selectionQuery: string, stepKey: string) {
  return `(${selectionQuery}) and not name:"${stepKey}"`;
}

function addStepToSelection(selectionQuery: string, stepKey: string) {
  return `(${selectionQuery}) or name:"${stepKey}"`;
}
