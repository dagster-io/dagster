import {Box, Colors, ErrorBoundary, NonIdealState} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import {CapturedOrExternalLogPanel} from './CapturedLogPanel';
import {LogFilter, LogsProviderLogs} from './LogsProvider';
import {LogsScrollingTable} from './LogsScrollingTable';
import {LogType, LogsToolbar} from './LogsToolbar';
import {IRunMetadataDict} from './RunMetadataProvider';
import {runsPathWithFilters} from './RunsFilterUtils';
import {toGraphQueryItems} from '../gantt/toGraphQueryItems';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import {filterRunSelectionByQuery} from '../run-selection/AntlrRunSelection';
import {RunDagsterRunEventFragment, RunPageFragment} from './types/RunFragments.types';
import {useComputeLogFileKeyForSelection} from './useComputeLogFileKeyForSelection';

/** Props shared by the desktop and mobile bodies of the run page. */
export interface RunViewProps {
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

/** State behind the logs panel: log type, step selection, and compute log file. */
export const useRunLogsView = ({
  run,
  metadata,
  logsFilter,
  selectionQuery,
}: Pick<RunViewProps, 'run' | 'metadata' | 'logsFilter' | 'selectionQuery'>) => {
  const [queryLogType, setQueryLogType] = useQueryPersistedState<string>({
    queryKey: 'logType',
    defaults: {logType: LogType.structured},
  });

  const logType = logTypeFromQuery(queryLogType);
  const setLogType = (lt: LogType) => setQueryLogType(LogType[lt]);
  const [computeLogUrl, setComputeLogUrl] = useState<string | null>(null);

  const stepKeysJSON = JSON.stringify(Object.keys(metadata.steps).sort());
  const stepKeys: string[] = useMemo(() => JSON.parse(stepKeysJSON), [stepKeysJSON]);

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

  return {
    logType,
    setLogType,
    computeLogUrl,
    setComputeLogUrl,
    stepKeys,
    runtimeGraph,
    selectionStepKeys,
    selection,
    logCaptureInfo,
    computeLogFileKey,
    setComputeLogFileKey,
    logsFilterStepKeys,
  };
};

export type RunLogsViewState = ReturnType<typeof useRunLogsView>;

/** The logs toolbar and the selected log view, shared by the desktop and mobile run pages. */
export const RunLogsPanel = ({
  className,
  view,
  expand,
  ...rest
}: Pick<RunViewProps, 'run' | 'runId' | 'logs' | 'logsFilter' | 'metadata' | 'onSetLogsFilter'> & {
  className?: string;
  view: RunLogsViewState;
  expand?: {isSectionExpanded: boolean; toggleExpanded: () => void};
}) => (
  <ErrorBoundary region="logs">
    <div className={className}>
      <LogsToolbar
        logType={view.logType}
        onSetLogType={view.setLogType}
        filter={rest.logsFilter}
        onSetFilter={rest.onSetLogsFilter}
        steps={view.stepKeys}
        metadata={rest.metadata}
        computeLogFileKey={view.computeLogFileKey}
        onSetComputeLogKey={view.setComputeLogFileKey}
        computeLogUrl={view.computeLogUrl}
        counts={rest.logs.counts}
        {...expand}
      />
      <RunLogsContent {...rest} view={view} />
    </div>
  </ErrorBoundary>
);

const RunLogsContent = ({
  run,
  runId,
  logs,
  logsFilter,
  metadata,
  view,
}: Pick<RunViewProps, 'run' | 'runId' | 'logs' | 'logsFilter' | 'metadata'> & {
  view: RunLogsViewState;
}) => {
  const {logType, logsFilterStepKeys, computeLogFileKey, logCaptureInfo, setComputeLogUrl} = view;

  if (run?.status === 'QUEUED') {
    return (
      <NonIdealState
        icon="arrow_forward"
        title="Run queued"
        description="This run is queued for execution and will start soon."
        action={
          <Link to={runsPathWithFilters([{token: 'status', value: 'QUEUED'}])}>
            View queued runs
          </Link>
        }
      />
    );
  }
  if (logType === LogType.structured) {
    return (
      <LogsScrollingTable
        logs={logs}
        filter={logsFilter}
        filterStepKeys={logsFilterStepKeys}
        filterKey={`${JSON.stringify(logsFilter)}`}
        metadata={metadata}
      />
    );
  }
  if (computeLogFileKey) {
    return (
      <CapturedOrExternalLogPanel
        logKey={computeLogFileKey ? [runId, 'compute_logs', computeLogFileKey] : []}
        logCaptureInfo={logCaptureInfo}
        visibleIOType={LogType[logType]}
        onSetDownloadUrl={setComputeLogUrl}
      />
    );
  }
  return <NoStepSelectionState type={logType} />;
};

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
        description="Select a step from the dropdown above to view logs."
      />
    </Box>
  );
};
