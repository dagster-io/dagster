import {ErrorBoundary, Tab, Tabs} from '@dagster-io/ui-components';
import {ComponentProps, useEffect, useState} from 'react';

import {RunActionButtons} from './RunActionButtons';
import {RunHeaderTags} from './RunHeaderTags';
import {RunLogsPanel, RunViewProps, useRunLogsView} from './RunLogsView';
import {activeStatuses, failedStatuses} from './RunStatuses';
import {useRunRepoInfo} from './useRunRepoInfo';
import {GanttStatusPanel} from '../gantt/GanttStatusPanel';
import {useQueryPersistedState} from '../hooks/useQueryPersistedState';
import styles from './css/MobileRun.module.css';
import {matchingComputeLogKeyFromStepKey} from './useComputeLogFileKeyForSelection';

type MobileRunTab = 'logs' | 'steps' | 'details';

/**
 * Mobile body of the run page: logs, step status, and the run's header tags as tabs. The Gantt
 * chart and split panels are left out.
 */
export const MobileRunWithData = (props: RunViewProps) => {
  const {run, runId, logs, logsFilter, metadata, onSetLogsFilter} = props;
  // Mobile never selects steps (see onClickStep), so a `?selection=` from a desktop link is
  // ignored rather than silently changing what Re-execute does.
  const view = useRunLogsView({run, metadata, logsFilter, selectionQuery: ''});
  const {repoAddress, isJob} = useRunRepoInfo(run);

  // Chosen once, so the tab doesn't switch out from under you when the run finishes.
  const [defaultTab] = useState<MobileRunTab>(() =>
    run && (failedStatuses.has(run.status) || activeStatuses.has(run.status)) ? 'steps' : 'logs',
  );
  const [tab, setTab] = useQueryPersistedState<MobileRunTab>({
    queryKey: 'tab',
    defaults: {tab: defaultTab},
  });

  // Filters the logs to the step rather than selecting it: there's no Gantt chart to show or
  // clear a selection.
  const onClickStep = (stepKey: string) => {
    onSetLogsFilter({...logsFilter, logQuery: [{token: 'query', value: `name:"${stepKey}"`}]});
    const matchingLogKey = matchingComputeLogKeyFromStepKey(metadata.logCaptureSteps, stepKey);
    if (matchingLogKey) {
      view.setComputeLogFileKey(matchingLogKey);
    }
    setTab('logs');
  };

  const tabContent = () => {
    if (tab === 'details') {
      return (
        <div className={styles.details}>
          {run ? (
            <RunHeaderTags run={run} repoAddress={repoAddress} isJob={isJob} loading={false} />
          ) : null}
        </div>
      );
    }
    if (tab === 'steps') {
      return (
        <div className={styles.steps}>
          <ErrorBoundary region="steps">
            <MobileRunSteps
              runId={runId}
              graph={view.runtimeGraph ?? []}
              metadata={metadata}
              selection={view.selection}
              onClickStep={onClickStep}
            />
          </ErrorBoundary>
        </div>
      );
    }
    return (
      <RunLogsPanel
        className={styles.logs}
        run={run}
        runId={runId}
        logs={logs}
        logsFilter={logsFilter}
        metadata={metadata}
        onSetLogsFilter={onSetLogsFilter}
        view={view}
      />
    );
  };

  return (
    <div className={styles.container}>
      <div className={styles.tabRow}>
        <Tabs selectedTabId={tab} onChange={setTab}>
          <Tab id="logs" title="Logs" />
          <Tab id="steps" title="Steps" />
          <Tab id="details" title="Details" />
        </Tabs>
        {run && view.runtimeGraph ? (
          <RunActionButtons
            run={run}
            graph={view.runtimeGraph}
            metadata={metadata}
            selection={view.selection}
          />
        ) : null}
      </div>
      {tabContent()}
    </div>
  );
};

/** The step status list, ticking once a second for step durations until the run exits. */
const MobileRunSteps = (props: Omit<ComponentProps<typeof GanttStatusPanel>, 'nowMs'>) => {
  const exitedAt = props.metadata.exitedAt;
  const [nowMs, setNowMs] = useState(() => Date.now());
  useEffect(() => {
    if (exitedAt) {
      return;
    }
    const interval = setInterval(() => setNowMs(Date.now()), 1000);
    return () => clearInterval(interval);
  }, [exitedAt]);
  return <GanttStatusPanel {...props} nowMs={exitedAt || nowMs} />;
};
