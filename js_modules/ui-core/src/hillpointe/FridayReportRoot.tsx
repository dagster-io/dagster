import {Box, Button, Icon, NonIdealState, Spinner, Tag} from '@dagster-io/ui-components';
import {ReactNode, useContext, useEffect, useState} from 'react';

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

type LogRow = {
  id: number;
  job: string;
  startedAt: string | null;
  finishedAt: string | null;
  success: boolean | null;
};

type RestoreRow = {job: string; runAt: string | null; status: string | null};

type TagLook = {
  intent: 'success' | 'danger' | 'warning' | 'primary' | 'none';
  icon: 'check_circle' | 'error' | 'warning' | 'run' | 'schedule' | 'cancel';
};

const STATUS_TAG: Record<Status, TagLook> = {
  OK: {intent: 'success', icon: 'check_circle'},
  FAILED: {intent: 'danger', icon: 'error'},
  EMPTY: {intent: 'warning', icon: 'warning'},
  RUNNING: {intent: 'primary', icon: 'run'},
  MISSING: {intent: 'none', icon: 'schedule'},
};

// SQL Agent run_status labels, as the msdb query spells them.
const RESTORE_TAG: Record<string, TagLook> = {
  Succeeded: STATUS_TAG.OK,
  Failed: STATUS_TAG.FAILED,
  Retry: STATUS_TAG.EMPTY,
  Canceled: {intent: 'none', icon: 'cancel'},
  'In Progress': STATUS_TAG.RUNNING,
};

const etTime = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York',
  hour: 'numeric',
  minute: '2-digit',
  second: '2-digit',
});
const etDateTime = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York',
  month: 'short',
  day: 'numeric',
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

/**
 * Start of this week's window (Saturday 00:00 UTC of the current Monday–Sunday
 * week), `weeksBack` weeks earlier. During the week that is the coming Friday
 * night, so the page shows every step as missing until tonight's batch runs.
 */
const windowStart = (weeksBack: number) => {
  const d = new Date();
  d.setUTCHours(0, 0, 0, 0);
  const isoWeekday = ((d.getUTCDay() + 6) % 7) + 1;
  d.setUTCDate(d.getUTCDate() - isoWeekday + 6);
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

/** Fetches a JSON endpoint on mount and every REFRESH_MS. A null url fetches nothing. */
const useJson = <T,>(url: string | null) => {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  useEffect(() => {
    if (!url) {
      return;
    }
    let cancelled = false;
    const load = async () => {
      try {
        const res = await fetch(url);
        const body = res.headers.get('content-type')?.includes('json') ? await res.json() : null;
        if (!res.ok) {
          throw new Error(body?.error ?? `${res.status} ${res.statusText}`);
        }
        if (!cancelled) {
          setData(body);
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
    setData(null);
    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [url]);

  return {data, error, updatedAt};
};

/** Error state, spinner, or the loaded content. */
const Loaded = ({
  error,
  ready,
  title,
  children,
}: {
  error: string | null;
  ready: boolean;
  title: string;
  children: ReactNode;
}) => {
  if (error) {
    return (
      <Box padding={48}>
        <NonIdealState icon="error" title={title} description={error} />
      </Box>
    );
  }
  if (!ready) {
    return (
      <Box flex={{justifyContent: 'center'}} padding={48}>
        <Spinner purpose="page" />
      </Box>
    );
  }
  return <>{children}</>;
};

const StatusCell = ({look, label}: {look: TagLook; label: string}) => (
  <td>
    <Tag intent={look.intent} icon={look.icon}>
      {label}
    </Tag>
  </td>
);

const FridayReportRoot = () => {
  useTrackPageView();
  useDocumentTitle('Friday report');
  const {basePath} = useContext(AppContext);

  const [weeksBack, setWeeksBack] = useState(0);
  // 'friday' hides the raw log and the Realpage restore history.
  const [view, setView] = useState<'all' | 'friday'>('all');

  const start = windowStart(weeksBack);
  const end = new Date(start.getTime() + WINDOW_HOURS * 3600 * 1000);

  const report = useJson<{jobs: ReportJob[]}>(
    `${basePath}/hillpointe/friday_report?start=${start.toISOString()}&end=${end.toISOString()}`,
  );
  const log = useJson<{rows: LogRow[]}>(
    view === 'all' ? `${basePath}/hillpointe/entrata_api_log` : null,
  );
  const restore = useJson<{rows: RestoreRow[]}>(
    view === 'all' ? `${basePath}/hillpointe/realpage_restore` : null,
  );

  const jobs = report.data?.jobs ?? [];
  const started = jobs.map((j) => j.startedAt).filter((s): s is string => !!s);
  const finished = jobs.map((j) => j.finishedAt).filter((s): s is string => !!s);
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
          {report.updatedAt ? (
            <span className={styles.muted}>Updated {etClock.format(report.updatedAt)} ET</span>
          ) : null}
          <Button
            icon={<Icon name={view === 'all' ? 'filter_alt' : 'view_list'} />}
            onClick={() => setView(view === 'all' ? 'friday' : 'all')}
          >
            {view === 'all' ? 'Friday batch only' : 'Show everything'}
          </Button>
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

      <Loaded error={report.error} ready={!!report.data} title="Could not load the Friday report">
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
                {jobs.map((j) => (
                  <tr key={j.job}>
                    <td className={styles.muted}>{j.step}</td>
                    <td>{j.job}</td>
                    <StatusCell
                      look={STATUS_TAG[j.status] ?? STATUS_TAG.MISSING}
                      label={j.status}
                    />
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
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Loaded>

      {view === 'all' ? (
        <>
          <div className={styles.card}>
            <div className={styles.cardTitle}>
              Realpage restore
              <span className={styles.cardSub}>
                SQL Agent history of RestoreRealpageDaily · server clock
              </span>
            </div>
            <Loaded
              error={restore.error}
              ready={!!restore.data}
              title="Could not load the Realpage restore history"
            >
              <div className={styles.tableWrap}>
                <table className={styles.timingsTable}>
                  <thead>
                    <tr>
                      <th>Job</th>
                      <th>Run time</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(restore.data?.rows ?? []).map((r, i) => (
                      <tr key={`${r.runAt}-${i}`}>
                        <td>{r.job}</td>
                        <td className={styles.fridayTime}>
                          {r.runAt ? r.runAt.slice(0, 19).replace('T', ' ') : '—'}
                        </td>
                        <StatusCell
                          look={RESTORE_TAG[r.status ?? ''] ?? STATUS_TAG.MISSING}
                          label={r.status ?? 'Unknown'}
                        />
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Loaded>
          </div>

          <div className={styles.card}>
            <div className={styles.cardTitle}>
              Entrata API log
              <span className={styles.cardSub}>
                Newest {log.data?.rows.length ?? ''} rows of dev.entrata_report_api_log, newest
                first
              </span>
            </div>
            <Loaded error={log.error} ready={!!log.data} title="Could not load the API log">
              <div className={styles.fridayLog}>
                <table className={styles.timingsTable}>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Job</th>
                      <th>Started (ET)</th>
                      <th>Finished (ET)</th>
                      <th>Result</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(log.data?.rows ?? []).map((r) => {
                      const status: Status =
                        r.finishedAt === null ? 'RUNNING' : r.success ? 'OK' : 'FAILED';
                      return (
                        <tr key={r.id}>
                          <td className={styles.muted}>{r.id}</td>
                          <td>{r.job}</td>
                          <td className={styles.fridayTime}>
                            {r.startedAt ? etDateTime.format(new Date(r.startedAt)) : '—'}
                          </td>
                          <td className={styles.fridayTime}>
                            {r.finishedAt ? etDateTime.format(new Date(r.finishedAt)) : '—'}
                          </td>
                          <StatusCell look={STATUS_TAG[status]} label={status} />
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Loaded>
          </div>
        </>
      ) : null}
    </div>
  );
};

// eslint-disable-next-line import/no-default-export
export default FridayReportRoot;
