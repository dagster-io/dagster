import {Button, Icon, NonIdealState, Spinner, showToast} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {ReactNode, useMemo, useState} from 'react';
import {useParams} from 'react-router-dom';

import {gql, useMutation, useQuery} from '../../apollo-client';
import {formatElapsedTimeWithoutMsec} from '../Util';
import styles from './css/Mobile.module.css';
import {MobileRunQuery, MobileRunQueryVariables} from './types/MobileRun.types';
import {LogLevel, StepEventStatus, TerminateRunPolicy} from '../../graphql/types';
import {useConfirmation} from '../CustomConfirmationProvider';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {RunStatusTag} from '../../runs/RunStatusTag';
import {doneStatuses} from '../../runs/RunStatuses';
import {TERMINATE_MUTATION} from '../../runs/RunUtils';
import {TimeElapsed} from '../../runs/TimeElapsed';
import {TerminateMutation, TerminateMutationVariables} from '../../runs/types/RunUtils.types';
import {TimeFromNow} from '../../ui/TimeFromNow';
import {useQueryRefreshAtInterval} from '../QueryRefresh';

const FIVE_SECONDS = 5000;
// The backend caps a logs page at 1000 events.
const LOG_LIMIT = 1000;
const LOG_TAIL = 60;

const NOISY_EVENT_TYPES = new Set(['ASSET_MATERIALIZATION_PLANNED']);

// Structured events have an empty message; describe them by type instead.
const labelForEventType = (eventType: string | null) =>
  eventType ? eventType.toLowerCase().replace(/_/g, ' ') : '';

const STEP_ICON: Record<StepEventStatus, string | undefined> = {
  [StepEventStatus.SUCCESS]: styles.stepSuccess,
  [StepEventStatus.FAILURE]: styles.stepFailure,
  [StepEventStatus.IN_PROGRESS]: styles.stepRunning,
  [StepEventStatus.SKIPPED]: styles.stepSkipped,
};

// eslint-disable-next-line import/no-default-export
export default function MobileRun() {
  const {runId} = useParams<{runId: string}>();
  useDocumentTitle(`Run ${runId.slice(0, 8)}`);

  const queryResult = useQuery<MobileRunQuery, MobileRunQueryVariables>(MOBILE_RUN_QUERY, {
    variables: {runId, logLimit: LOG_LIMIT},
  });
  useQueryRefreshAtInterval(queryResult, FIVE_SECONDS);
  const {data, loading} = queryResult;

  const run = data?.runOrError.__typename === 'Run' ? data.runOrError : null;
  const logs = useMemo(() => {
    const conn = data?.logsForRun;
    if (conn?.__typename !== 'EventConnection') {
      return [];
    }
    // Step events are logged at debug level, so every level is shown. Planning
    // events are dropped: a run emits one per asset the moment it is created,
    // which buries everything else. Newest first.
    return conn.events
      .filter((e) => !NOISY_EVENT_TYPES.has(e.eventType ?? ''))
      .map((e) => ({...e, text: e.message || labelForEventType(e.eventType)}))
      .filter((e) => e.text)
      .slice(-LOG_TAIL)
      .reverse();
  }, [data]);

  const [terminate, {loading: terminating}] = useMutation<
    TerminateMutation,
    TerminateMutationVariables
  >(TERMINATE_MUTATION);

  const confirm = useConfirmation();

  const onTerminate = async (terminatePolicy: TerminateRunPolicy) => {
    if (terminatePolicy === TerminateRunPolicy.MARK_AS_CANCELED_IMMEDIATELY) {
      try {
        await confirm({
          title: 'Force terminate?',
          description:
            'Marks the run as canceled right away without waiting for its steps to stop. Use this when a normal terminate is stuck; the job may keep running in the background until it exits on its own.',
          buttonText: 'Force terminate',
          catchOnCancel: true,
          style: {width: 'min(94vw, 480px)'},
        });
      } catch {
        return;
      }
    }
    const result = await terminate({variables: {runIds: [runId], terminatePolicy}});
    const outcome = result.data?.terminateRuns;
    const first =
      outcome?.__typename === 'TerminateRunsResult' ? outcome.terminateRunResults[0] : null;
    if (first?.__typename === 'TerminateRunSuccess') {
      await showToast({intent: 'success', message: 'Termination requested'});
      queryResult.refetch();
    } else {
      const message = first && 'message' in first ? first.message : 'Could not terminate run';
      await showToast({intent: 'danger', message});
    }
  };

  if (!run) {
    if (loading) {
      return (
        <div className={styles.center}>
          <Spinner purpose="page" />
        </div>
      );
    }
    return <NonIdealState icon="run" title="Run not found" />;
  }

  const duration =
    run.startTime && run.endTime
      ? formatElapsedTimeWithoutMsec((run.endTime - run.startTime) * 1000)
      : null;

  return (
    <div className={styles.runPage}>
      <div className={styles.runHeader}>
        <div className={styles.cardName}>{run.pipelineName}</div>
        <div className={styles.cardStatus}>
          <RunStatusTag status={run.status} />
          {run.startTime ? (
            <span className={styles.cardMeta}>
              <TimeFromNow unixTimestamp={run.startTime} />
              {duration ? ` · ${duration}` : ''}
              {!run.endTime ? (
                <span className={styles.live}>
                  · <TimeElapsed startUnix={run.startTime} endUnix={null} />
                </span>
              ) : null}
            </span>
          ) : null}
        </div>
        <div className={styles.cardMeta}>{run.runId}</div>
        {/* The server only offers a normal terminate for queued or started runs,
            but a forced cancel is allowed on any unfinished run, including one
            stuck in Starting or Canceling. */}
        {!doneStatuses.has(run.status) ? (
          <div className={styles.actions}>
            {run.canTerminate ? (
              <Button
                intent="danger"
                icon={<Icon name="cancel" />}
                loading={terminating}
                onClick={() => onTerminate(TerminateRunPolicy.SAFE_TERMINATE)}
                className={styles.runButton}
              >
                Terminate
              </Button>
            ) : null}
            <Button
              icon={<Icon name="warning" />}
              loading={terminating}
              onClick={() => onTerminate(TerminateRunPolicy.MARK_AS_CANCELED_IMMEDIATELY)}
              className={styles.runButton}
            >
              Force terminate
            </Button>
          </div>
        ) : null}
      </div>

      <Section title="Steps" count={run.stepStats.length}>
        {run.stepStats.length ? (
          <div className={styles.steps}>
            {run.stepStats.map((step) => (
              <div key={step.stepKey} className={styles.step}>
                <span
                  className={clsx(styles.stepDot, step.status ? STEP_ICON[step.status] : null)}
                />
                <span className={styles.stepKey}>{step.stepKey}</span>
                <span className={styles.cardMeta}>
                  {step.startTime && step.endTime ? (
                    formatElapsedTimeWithoutMsec((step.endTime - step.startTime) * 1000)
                  ) : step.startTime && step.status === StepEventStatus.IN_PROGRESS ? (
                    <TimeElapsed startUnix={step.startTime} endUnix={null} />
                  ) : (
                    ''
                  )}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className={styles.emptyNote}>No steps have started yet.</div>
        )}
      </Section>

      <Section title="Logs" count={logs.length}>
        {logs.length ? (
          <div className={styles.logs}>
            {logs.map((e, i) => (
              <div key={`${e.timestamp}-${i}`} className={styles.logLine}>
                <span className={styles.logTime}>
                  {new Date(Number(e.timestamp)).toLocaleTimeString()}
                </span>
                <span
                  className={clsx(
                    styles.logLevel,
                    e.level === LogLevel.ERROR || e.level === LogLevel.CRITICAL
                      ? styles.logError
                      : e.level === LogLevel.WARNING
                        ? styles.logWarning
                        : null,
                  )}
                >
                  {e.level}
                </span>
                {e.stepKey ? <span className={styles.logStep}>{e.stepKey}</span> : null}
                <span className={styles.logMessage}>{e.text}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className={styles.emptyNote}>No log messages yet.</div>
        )}
      </Section>
    </div>
  );
}

// A titled block that folds away when its header is tapped.
const Section = ({title, count, children}: {title: string; count: number; children: ReactNode}) => {
  const [open, setOpen] = useState(true);
  return (
    <>
      <button type="button" className={styles.sectionTitle} onClick={() => setOpen((o) => !o)}>
        <Icon name={open ? 'expand_more' : 'chevron_right'} />
        {title}
        <span className={styles.sectionCount}>{count}</span>
      </button>
      {open ? children : null}
    </>
  );
};

export const MOBILE_RUN_QUERY = gql`
  query MobileRunQuery($runId: ID!, $logLimit: Int!) {
    runOrError(runId: $runId) {
      ... on Run {
        id
        runId
        status
        pipelineName
        startTime
        endTime
        canTerminate
        stepStats {
          stepKey
          status
          startTime
          endTime
        }
      }
    }
    logsForRun(runId: $runId, limit: $logLimit) {
      ... on EventConnection {
        hasMore
        events {
          ... on MessageEvent {
            message
            timestamp
            level
            stepKey
            eventType
          }
        }
      }
    }
  }
`;
