import {Box, Button, Icon, NonIdealState, Spinner, Tag} from '@dagster-io/ui-components';
import {useContext, useEffect, useState} from 'react';

import {formatDuration} from './HillpointeRoot';
import styles from './css/HillpointeRoot.module.css';
import {AppContext} from '../app/AppContext';
import {useTrackPageView} from '../app/analytics';
import {useDocumentTitle} from '../hooks/useDocumentTitle';

// The batch runs Friday evening Eastern: Saturday 00:00–04:00 UTC, as in FridayReports.xlsx.
const WINDOW_HOURS = 4;
const REFRESH_MS = 30_000;
const WEEK_MS = 7 * 24 * 3600 * 1000;

type Status = 'OK' | 'FAILED' | 'EMPTY' | 'MISSING' | 'RUNNING';

type ReportJob = {
  step: number;
  job: string;
  status: Status;
  startedAt: string | null;
  finishedAt: string | null;
  durationSeconds: number | null;
  message: string | null;
};

const STATUS_TAG: Record<
  Status,
  {
    intent: 'success' | 'danger' | 'warning' | 'primary' | 'none';
    icon: 'check_circle' | 'error' | 'warning' | 'run' | 'schedule';
  }
> = {
  OK: {intent: 'success', icon: 'check_circle'},
  FAILED: {intent: 'danger', icon: 'error'},
  EMPTY: {intent: 'warning', icon: 'warning'},
  RUNNING: {intent: 'primary', icon: 'run'},
  MISSING: {intent: 'none', icon: 'schedule'},
};

const etTime = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York',
  hour: 'numeric',
  minute: '2-digit',
  second: '2-digit',
});
const etClock = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York',
  hour: 'numeric',
  minute: '2-digit',
});
const etDate = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York',
  weekday: 'long',
  month: 'short',
  day: 'numeric',
  year: 'numeric',
});

/** Start of the latest Saturday 00:00 UTC window that has begun, `weeksBack` weeks earlier. */
const windowStart = (weeksBack: number) => {
  const d = new Date();
  d.setUTCHours(0, 0, 0, 0);
  d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 1) % 7));
  return new Date(d.getTime() - weeksBack * WEEK_MS);
};

const headline = (jobs: ReportJob[]) => {
  const count = (s: Status) => jobs.filter((j) => j.status === s).length;
  if (count('FAILED')) {
    return (
      <Tag intent="danger" icon="error">
        Needs attention
      </Tag>
    );
  }
  if (count('RUNNING')) {
    return (
      <Tag intent="primary" icon="run">
        Still running
      </Tag>
    );
  }
  if (count('MISSING') === jobs.length) {
    return <Tag icon="schedule">Not started</Tag>;
  }
  if (count('MISSING') || count('EMPTY')) {
    return (
      <Tag intent="warning" icon="warning">
        Incomplete
      </Tag>
    );
  }
  return (
    <Tag intent="success" icon="check_circle">
      All clear
    </Tag>
  );
};

const FridayReportRoot = () => {
  useTrackPageView();
  useDocumentTitle('Friday report');
  const {basePath} = useContext(AppContext);

  const [weeksBack, setWeeksBack] = useState(0);
  const [jobs, setJobs] = useState<ReportJob[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const start = windowStart(weeksBack);
      const end = new Date(start.getTime() + WINDOW_HOURS * 3600 * 1000);
      const url = `${basePath}/hillpointe/friday_report?start=${start.toISOString()}&end=${end.toISOString()}`;
      try {
        const res = await fetch(url);
        const body = res.headers.get('content-type')?.includes('json') ? await res.json() : null;
        if (!res.ok) {
          throw new Error(body?.error ?? `${res.status} ${res.statusText}`);
        }
        if (!cancelled) {
          setJobs(body.jobs);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : String(e));
        }
      }
      if (!cancelled) {
        setUpdatedAt(new Date());
      }
    };
    setJobs(null);
    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [basePath, weeksBack]);

  const start = windowStart(weeksBack);
  const end = new Date(start.getTime() + WINDOW_HOURS * 3600 * 1000);

  const started = (jobs ?? []).map((j) => j.startedAt).filter((s): s is string => !!s);
  const finished = (jobs ?? []).map((j) => j.finishedAt).filter((s): s is string => !!s);
  const elapsed =
    started.length && finished.length
      ? (Math.max(...finished.map(Date.parse)) - Math.min(...started.map(Date.parse))) / 1000
      : null;

  return (
    <div className={styles.page}>
      <Box flex={{justifyContent: 'space-between', alignItems: 'center', wrap: 'wrap', gap: 12}}>
        <div className={styles.cardTitle}>
          Friday report
          <span className={styles.cardSub}>
            Entrata API batch · {etDate.format(start)} {etClock.format(start)}–{etClock.format(end)}{' '}
            ET
          </span>
        </div>
        <Box flex={{alignItems: 'center', gap: 8}}>
          {updatedAt ? (
            <span className={styles.muted}>Updated {etClock.format(updatedAt)} ET</span>
          ) : null}
          <Button icon={<Icon name="arrow_back" />} onClick={() => setWeeksBack((w) => w + 1)}>
            Previous week
          </Button>
          <Button
            rightIcon={<Icon name="arrow_forward" />}
            disabled={weeksBack === 0}
            onClick={() => setWeeksBack((w) => w - 1)}
          >
            {weeksBack === 1 ? 'Latest' : 'Next week'}
          </Button>
        </Box>
      </Box>

      {error ? (
        <Box padding={64}>
          <NonIdealState
            icon="error"
            title="Could not load the Friday report"
            description={error}
          />
        </Box>
      ) : !jobs ? (
        <Box flex={{justifyContent: 'center'}} padding={64}>
          <Spinner purpose="page" />
        </Box>
      ) : (
        <>
          <div className={styles.tiles}>
            <div className={styles.tile}>
              <div className={styles.tileLabel}>Batch</div>
              <div className={styles.tileValue}>{headline(jobs)}</div>
            </div>
            {(['OK', 'FAILED', 'EMPTY', 'MISSING'] as Status[]).map((s) => (
              <div key={s} className={styles.tile}>
                <div className={styles.tileLabel}>{s.charAt(0) + s.slice(1).toLowerCase()}</div>
                <div className={styles.tileValue}>{jobs.filter((j) => j.status === s).length}</div>
              </div>
            ))}
            <div className={styles.tile}>
              <div className={styles.tileLabel}>Batch elapsed</div>
              <div className={styles.tileValue}>{formatDuration(elapsed)}</div>
            </div>
          </div>

          <div className={styles.card}>
            <div className={styles.cardTitle}>
              Steps
              <span className={styles.cardSub}>Latest run of each job inside the window</span>
            </div>
            <div className={styles.tableWrap}>
              <table className={styles.timingsTable}>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Job</th>
                    <th>Status</th>
                    <th>Started (ET)</th>
                    <th>Finished (ET)</th>
                    <th>Duration</th>
                    <th>Message</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((j) => {
                    const tag = STATUS_TAG[j.status] ?? STATUS_TAG.MISSING;
                    return (
                      <tr key={j.job}>
                        <td className={styles.muted}>{j.step}</td>
                        <td>{j.job}</td>
                        <td>
                          <Tag intent={tag.intent} icon={tag.icon}>
                            {j.status}
                          </Tag>
                        </td>
                        <td className={styles.fridayTime}>
                          {j.startedAt ? etTime.format(new Date(j.startedAt)) : '—'}
                        </td>
                        <td className={styles.fridayTime}>
                          {j.finishedAt ? etTime.format(new Date(j.finishedAt)) : '—'}
                        </td>
                        <td>{formatDuration(j.durationSeconds)}</td>
                        <td className={styles.fridayMessage} title={j.message ?? undefined}>
                          {j.message ?? ''}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// eslint-disable-next-line import/no-default-export
export default FridayReportRoot;
