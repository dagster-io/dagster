import {
  Box,
  Button,
  ErrorBoundary,
  Icon,
  NonIdealState,
  SplitPanelContainer,
  SplitPanelContainerHandle,
  Tooltip,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {memo, useLayoutEffect, useMemo, useRef, useState} from 'react';

import {LogsProvider, LogsProviderLogs} from './LogsProvider';
import {MobileRunWithData} from './MobileRun';
import {RunActionButtons} from './RunActionButtons';
import {RunContext} from './RunContext';
import {RunLogsPanel, RunViewProps, useRunLogsView} from './RunLogsView';
import {IRunMetadataDict, RunMetadataProvider} from './RunMetadataProvider';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {RunDagsterRunEventFragment, RunPageFragment} from './types/RunFragments.types';
import {useIsMobile} from '../app/layout/IsMobileContext';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {GanttChart, GanttChartLoadingState, GanttChartMode} from '../gantt/GanttChart';
import {RunStatus} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useFavicon} from '../hooks/useFavicon';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {CompletionType, useTraceDependency} from '../performance/TraceContext';
import styles from './css/Run.module.css';
import {matchingComputeLogKeyFromStepKey} from './useComputeLogFileKeyForSelection';
import {useQueryPersistedLogFilter} from './useQueryPersistedLogFilter';
import {shortenId} from '../util/shortenId';

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
    case RunStatus.SUSPENDED:
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

  const documentTitle = useMemo(() => {
    const shortId = shortenId(runId);
    if (!run) {
      return `Runs | ${shortId}`;
    }
    if (isHiddenAssetGroupJob(run.pipelineName)) {
      return `Runs | ${shortId} [${run.status}]`;
    }
    return `Runs | ${run.pipelineName} | ${shortId} [${run.status}]`;
  }, [run, runId]);

  useDocumentTitle(documentTitle);
  useFavicon(run ? runStatusFavicon(run.status) : '/favicon.svg');

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
      logQuery: query && query !== '*' ? [{token: 'query', value: query}] : [],
    });
  };

  const logsDependency = useTraceDependency('RunLogs');
  const RunView = useIsMobile() ? MobileRunWithData : RunWithData;

  return (
    <RunContext.Provider value={run}>
      <LogsProvider key={runId} runId={runId}>
        {(logs) => (
          <>
            <OnLogsLoaded dependency={logsDependency} logs={logs} />
            <RunMetadataProvider logs={logs}>
              {(metadata) => (
                <RunView
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
const RunWithData = (props: RunViewProps) => {
  const {
    run,
    runId,
    logs,
    logsFilter,
    metadata,
    selectionQuery,
    onSetLogsFilter,
    onSetSelectionQuery,
  } = props;
  const view = useRunLogsView({run, metadata, logsFilter, selectionQuery});
  const {runtimeGraph, selectionStepKeys, selection, setComputeLogFileKey} = view;

  const onClickStep = (stepKey: string, evt: React.MouseEvent<any>) => {
    const index = selectionStepKeys.indexOf(stepKey);
    let nextSelectionQuery = selectionQuery;
    if (evt.shiftKey) {
      // shift-click to multi select steps, preserving quotations if present

      if (index !== -1) {
        // deselect the step if already selected
        nextSelectionQuery = removeStepFromSelection(nextSelectionQuery, stepKey);
      } else {
        // select the step otherwise
        nextSelectionQuery = addStepToSelection(nextSelectionQuery, stepKey);
      }
    } else {
      // If the step is already the only selected step, do nothing.
      if (selectionStepKeys.length === 1 && index !== -1) {
        return;
      }

      // select the step
      nextSelectionQuery = `name:"${stepKey}"`;

      // When only one step is selected, set the compute log key as well.
      const matchingLogKey = matchingComputeLogKeyFromStepKey(metadata.logCaptureSteps, stepKey);
      if (matchingLogKey) {
        setComputeLogFileKey(matchingLogKey);
      }
    }

    onSetSelectionQuery(nextSelectionQuery);
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
          <RunLogsPanel
            className={styles.logsContainer}
            run={run}
            runId={runId}
            logs={logs}
            logsFilter={logsFilter}
            metadata={metadata}
            onSetLogsFilter={onSetLogsFilter}
            view={view}
            expand={{
              isSectionExpanded: isBottomExpanded,
              toggleExpanded: isBottomExpanded ? resetPanels : expandBottomPanel,
            }}
          />
        }
      />
    </>
  );
};

function removeStepFromSelection(selectionQuery: string, stepKey: string) {
  return `(${selectionQuery}) and not name:"${stepKey}"`;
}

function addStepToSelection(selectionQuery: string, stepKey: string) {
  return `(${selectionQuery}) or name:"${stepKey}"`;
}
