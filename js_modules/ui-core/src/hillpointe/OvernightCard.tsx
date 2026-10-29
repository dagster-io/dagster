import {Tag} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import {gql, useQuery} from '../apollo-client';
import styles from './css/HillpointeRoot.module.css';
import {OvernightRunsQuery, OvernightRunsQueryVariables} from './types/OvernightCard.types';
import {RunStatus} from '../graphql/types';
import {RetriedTag, useRetriedSteps} from '../runs/RunRetriedTag';
import {RunStatusTag} from '../runs/RunStatusTag';

const RUNNING = new Set([
  RunStatus.QUEUED,
  RunStatus.NOT_STARTED,
  RunStatus.STARTING,
  RunStatus.STARTED,
  RunStatus.CANCELING,
]);

/**
 * The morning check: everything that ran since midnight, with the runs that
 * failed or only passed thanks to a retry listed so nobody has to open each one.
 */
export const OvernightCard = () => {
  // Midnight is taken once per mount; the poll keeps the list itself fresh.
  const [since] = useState(() => {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d.getTime() / 1000;
  });
  const {data} = useQuery<OvernightRunsQuery, OvernightRunsQueryVariables>(OVERNIGHT_RUNS_QUERY, {
    variables: {after: since},
    pollInterval: 15000,
  });
  const overnight = useMemo(
    () => (data?.runsOrError.__typename === 'Runs' ? data.runsOrError.results : []),
    [data],
  );
  const retriedSteps = useRetriedSteps(useMemo(() => overnight.map((r) => r.id), [overnight]));

  const failed = overnight.filter((r) => r.status === RunStatus.FAILURE);
  const running = overnight.filter((r) => RUNNING.has(r.status));
  const retried = overnight.filter((r) => retriedSteps.has(r.id));
  const attention = [...failed, ...retried.filter((r) => !failed.includes(r))].sort(
    (a, b) => b.creationTime - a.creationTime,
  );
  const lastFinished = Math.max(0, ...overnight.map((r) => r.endTime ?? 0));

  const tone = failed.length ? 'bad' : retried.length ? 'mixed' : 'good';
  const headline = !overnight.length
    ? {intent: 'none' as const, icon: 'schedule' as const, text: 'Nothing has run yet'}
    : failed.length
      ? {intent: 'danger' as const, icon: 'error' as const, text: 'Needs attention'}
      : retried.length
        ? {intent: 'warning' as const, icon: 'replay' as const, text: 'Passed with retries'}
        : running.length
          ? {intent: 'primary' as const, icon: 'run' as const, text: 'Still running'}
          : {intent: 'success' as const, icon: 'check_circle' as const, text: 'All clear'};

  return (
    <div className={clsx(styles.card, styles.overnight, styles[`overnight_${tone}`])}>
      <div className={styles.cardHeader}>
        <div className={styles.cardTitle}>
          Overnight
          <span className={styles.cardSub}>
            Since midnight
            {lastFinished
              ? ` · last run finished ${new Date(lastFinished * 1000).toLocaleTimeString(undefined, {hour: 'numeric', minute: '2-digit'})}`
              : ''}
          </span>
        </div>
        <Tag intent={headline.intent} icon={headline.icon}>
          {headline.text}
        </Tag>
      </div>
      <div className={styles.overnightStats}>
        <Stat value={overnight.length} label="runs" />
        <Stat value={failed.length} label="failed" tone={failed.length ? 'red' : undefined} />
        <Stat value={retried.length} label="retried" tone={retried.length ? 'yellow' : undefined} />
        <Stat value={running.length} label="still running" />
      </div>
      {attention.length ? (
        <div className={styles.attention}>
          {attention.map((run) => {
            const steps = retriedSteps.get(run.id);
            return (
              <div key={run.runId} className={styles.attentionRow}>
                <RunStatusTag status={run.status} />
                <RetriedTag steps={steps} short />
                <Link to={`/runs/${run.runId}`} className={styles.attentionJob}>
                  {run.jobName}
                </Link>
                <span className={styles.muted}>
                  {new Date(run.creationTime * 1000).toLocaleTimeString(undefined, {
                    hour: 'numeric',
                    minute: '2-digit',
                  })}
                  {steps?.length ? ` · retried: ${steps.join(', ')}` : ''}
                </span>
              </div>
            );
          })}
        </div>
      ) : overnight.length ? (
        <div className={styles.muted}>
          {running.length
            ? `${overnight.length - running.length} finished cleanly, ${running.length} still going.`
            : `All ${overnight.length} runs passed without a retry.`}
        </div>
      ) : (
        <div className={styles.muted}>No runs since midnight.</div>
      )}
    </div>
  );
};

const Stat = ({value, label, tone}: {value: number; label: string; tone?: 'red' | 'yellow'}) => (
  <div className={styles.stat}>
    <span
      className={clsx(
        styles.statValue,
        tone === 'red' && styles.statRed,
        tone === 'yellow' && styles.statYellow,
      )}
    >
      {value}
    </span>
    <span className={styles.statLabel}>{label}</span>
  </div>
);

export const OVERNIGHT_RUNS_QUERY = gql`
  query OvernightRunsQuery($after: Float!) {
    runsOrError(filter: {createdAfter: $after}, limit: 500) {
      ... on Runs {
        results {
          id
          runId
          jobName
          status
          creationTime
          endTime
        }
      }
    }
  }
`;
