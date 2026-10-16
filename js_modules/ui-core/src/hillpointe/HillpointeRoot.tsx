import {
  Box,
  Button,
  ButtonGroup,
  Colors,
  Icon,
  NonIdealState,
  Spinner,
  Table,
  Tag,
  Tooltip,
} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {ReactNode, useEffect, useMemo, useRef, useState} from 'react';
import {Link} from 'react-router-dom';

import {gql, useQuery} from '../apollo-client';
import styles from './css/HillpointeRoot.module.css';
import {
  HillpointeRowCountQuery,
  HillpointeRowCountQueryVariables,
  HillpointeRunHistoryQuery,
  HillpointeRunHistoryQueryVariables,
  HillpointeRunMetricsQuery,
  HillpointeRunMetricsQueryVariables,
  HillpointeRunStatsQuery,
  HillpointeRunStatsQueryVariables,
  HillpointeRunStepStatsQuery,
  HillpointeRunStepStatsQueryVariables,
  HillpointeSchedulesQuery,
  HillpointeSchedulesQueryVariables,
} from './types/HillpointeRoot.types';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {InstigationStatus, RunStatus, StepEventStatus} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {RunStatusTag} from '../runs/RunStatusTag';
import {TimeFromNow} from '../ui/TimeFromNow';

// Runs are scoped to the current month; the limit is a safety cap.
const MONTH_RUN_LIMIT = 5000;
const TABLE_ROWS = 50;
const TREND_DAYS = 30;
const ROLLING_DAYS = 7;
const HISTORY_DAYS = 90;

type Run = Extract<
  HillpointeRunMetricsQuery['runsOrError'],
  {__typename: 'Runs'}
>['results'][number];

type RunStats = {stepsSucceeded: number; stepsFailed: number; materializations: number};
/** Stats keyed by run id; null until the stats query has answered. */
type StatsByRun = Map<string, RunStats> | null;

// Status buckets. Colours are theme tokens, so every chart follows the selected theme.
type Bucket = 'success' | 'failure' | 'canceled' | 'inProgress' | 'queued';

const BUCKETS: {key: Bucket; label: string; color: string}[] = [
  {key: 'success', label: 'Succeeded', color: Colors.dataVizGreen()},
  {key: 'failure', label: 'Failed', color: Colors.dataVizRed()},
  {key: 'canceled', label: 'Canceled', color: Colors.dataVizGray()},
  {key: 'inProgress', label: 'In progress', color: Colors.dataVizBlue()},
  {key: 'queued', label: 'Queued', color: Colors.dataVizYellow()},
];

const bucketFor = (status: RunStatus): Bucket => {
  switch (status) {
    case RunStatus.SUCCESS:
      return 'success';
    case RunStatus.FAILURE:
      return 'failure';
    case RunStatus.CANCELED:
    case RunStatus.CANCELING:
      return 'canceled';
    case RunStatus.QUEUED:
    case RunStatus.NOT_STARTED:
      return 'queued';
    default:
      return 'inProgress';
  }
};

const STEP_COLOR: Record<StepEventStatus, string> = {
  [StepEventStatus.SUCCESS]: Colors.dataVizGreen(),
  [StepEventStatus.FAILURE]: Colors.dataVizRed(),
  [StepEventStatus.SKIPPED]: Colors.dataVizGray(),
  [StepEventStatus.IN_PROGRESS]: Colors.dataVizBlue(),
};

/** Seconds a run (or step) has taken so far, or null if it never started. */
export const durationSec = (start: number | null, end: number | null) =>
  start ? (end ?? Date.now() / 1000) - start : null;

export const formatDuration = (sec: number | null) => {
  if (sec === null) {
    return '—';
  }
  if (sec < 60) {
    return `${sec.toFixed(sec < 10 ? 1 : 0)}s`;
  }
  const m = Math.floor(sec / 60);
  if (m < 60) {
    return `${m}m ${Math.round(sec % 60)}s`;
  }
  return `${Math.floor(m / 60)}h ${m % 60}m`;
};

const dayKey = (d: Date) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;

export const HillpointeRoot = () => {
  useTrackPageView();
  useDocumentTitle('Hillpointe');

  // Fixed for the life of the page so the query variables stay stable.
  const [monthStart] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });
  const queryResult = useQuery<HillpointeRunMetricsQuery, HillpointeRunMetricsQueryVariables>(
    HILLPOINTE_RUN_METRICS_QUERY,
    {variables: {after: monthStart.getTime() / 1000, limit: MONTH_RUN_LIMIT}},
  );
  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  const {data, loading} = queryResult;
  const runs = useMemo(
    () => (data?.runsOrError.__typename === 'Runs' ? data.runsOrError.results : []),
    [data],
  );

  const statsResult = useQuery<HillpointeRunStatsQuery, HillpointeRunStatsQueryVariables>(
    HILLPOINTE_RUN_STATS_QUERY,
    {variables: {after: monthStart.getTime() / 1000, limit: MONTH_RUN_LIMIT}},
  );
  useQueryRefreshAtInterval(statsResult, FIFTEEN_SECONDS);
  const statsByRun: StatsByRun = useMemo(() => {
    const result = statsResult.data?.runsOrError;
    if (result?.__typename !== 'Runs') {
      return null;
    }
    const map = new Map<string, RunStats>();
    result.results.forEach((r) => {
      if (r.stats.__typename === 'RunStatsSnapshot') {
        map.set(r.runId, r.stats);
      }
    });
    return map;
  }, [statsResult.data]);

  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const selectedRun = runs.find((r) => r.runId === selectedRunId) ?? runs[0] ?? null;

  const content = () => {
    if (!data && loading) {
      return (
        <Box padding={64} flex={{justifyContent: 'center'}}>
          <Spinner purpose="page" />
        </Box>
      );
    }
    if (!runs.length) {
      return (
        <Box padding={64}>
          <NonIdealState
            icon="run"
            title="No runs yet"
            description="Launch a job and its metrics will show up here."
          />
        </Box>
      );
    }
    return (
      <div className={styles.page}>
        <Box flex={{justifyContent: 'flex-end'}}>
          <QueryRefreshCountdown refreshState={refreshState} />
        </Box>
        <SummaryTiles runs={runs} statsByRun={statsByRun} />
        <div className={styles.chartGrid}>
          <TrendCard runs={runs} />
          <div className={styles.stack}>
            <RunStatusBlock />
            <SuccessRateCard />
          </div>
        </div>
        {selectedRun ? (
          <RunBreakdown
            run={selectedRun}
            stats={statsByRun?.get(selectedRun.runId) ?? null}
            isLatest={selectedRun === runs[0]}
            onShowLatest={() => setSelectedRunId(null)}
          />
        ) : null}
        <RunsTable
          runs={runs}
          statsByRun={statsByRun}
          selectedRunId={selectedRun?.runId ?? null}
          onSelect={setSelectedRunId}
        />
      </div>
    );
  };

  return (
    <Box flex={{direction: 'column'}} style={{height: '100%', overflow: 'hidden'}}>
      {content()}
    </Box>
  );
};

const Tile = ({label, value, sub}: {label: string; value: ReactNode; sub?: string}) => (
  <div className={styles.tile}>
    <div className={styles.tileLabel}>{label}</div>
    <div className={styles.tileValue}>{value}</div>
    {sub ? <div className={styles.tileSub}>{sub}</div> : null}
  </div>
);

const COUNT_UP_MS = 900;
const percent = (n: number) => `${Math.round(n)}%`;
const whole = (n: number) => Math.round(n).toLocaleString();

/** A number that eases from its last value to the new one, so tiles tick instead of jump. */
const CountUp = ({value, format = whole}: {value: number; format?: (n: number) => string}) => {
  const [shown, setShown] = useState(0);
  const fromRef = useRef(0);
  useEffect(() => {
    const from = fromRef.current;
    const start = performance.now();
    let frame = 0;
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / COUNT_UP_MS);
      const eased = 1 - Math.pow(1 - p, 3);
      setShown(from + (value - from) * eased);
      if (p < 1) {
        frame = requestAnimationFrame(tick);
      } else {
        fromRef.current = value;
      }
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value]);
  return <span className={styles.countUp}>{format(shown)}</span>;
};

const SummaryTiles = ({runs, statsByRun}: {runs: Run[]; statsByRun: StatsByRun}) => {
  const monthLabel = new Date().toLocaleDateString(undefined, {month: 'long', year: 'numeric'});
  const counts = {success: 0, failure: 0, canceled: 0, inProgress: 0, queued: 0};
  runs.forEach((r) => counts[bucketFor(r.status)]++);
  // Canceled runs are neither passes nor failures, so they sit outside the rate.
  const finished = counts.success + counts.failure;
  const durations = runs
    .filter((r) => r.endTime)
    .map((r) => durationSec(r.startTime, r.endTime))
    .filter((d): d is number => d !== null);
  const avg = durations.length ? durations.reduce((a, b) => a + b, 0) / durations.length : null;
  const materializations = statsByRun
    ? runs.reduce((sum, r) => sum + (statsByRun.get(r.runId)?.materializations ?? 0), 0)
    : null;

  return (
    <div className={styles.tiles}>
      <Tile label="Runs" value={<CountUp value={runs.length} />} sub={monthLabel} />
      <Tile
        label="Success rate"
        value={
          finished ? <CountUp value={(counts.success / finished) * 100} format={percent} /> : '—'
        }
        sub={[
          `${counts.success} passed`,
          `${counts.failure} failed`,
          `${counts.canceled} canceled`,
          `${counts.inProgress + counts.queued} running`,
        ].join(' · ')}
      />
      <Tile
        label="Failed"
        value={<CountUp value={counts.failure} />}
        sub={`${counts.canceled} canceled`}
      />
      <Tile label="Avg duration" value={formatDuration(avg)} sub="Finished runs" />
      <Tile
        label="Active"
        value={<CountUp value={counts.inProgress + counts.queued} />}
        sub={`${counts.inProgress} running, ${counts.queued} queued`}
      />
      <Tile
        label="Materializations"
        value={materializations === null ? '…' : <CountUp value={materializations} />}
        sub="This month"
      />
    </div>
  );
};

const Legend = ({items}: {items: {label: string; color: string}[]}) => (
  <div className={styles.legend}>
    {items.map((item) => (
      <div key={item.label} className={styles.legendItem}>
        <span className={styles.swatch} style={{background: item.color}} />
        {item.label}
      </div>
    ))}
  </div>
);

type HistoryRun = Extract<
  HillpointeRunHistoryQuery['runsOrError'],
  {__typename: 'Runs'}
>['results'][number];

const EMPTY_DAY = Colors.backgroundLighter();
// Written by each copy step; the same label scripts/daily_row_totals.py sums.
const ROW_COUNT_LABEL = 'rows_copied';

// Share of finished runs that succeeded: at or above GOOD is green, at or above
// MIXED is yellow, below that is red.
const HEALTH_GOOD = 0.8;
const HEALTH_MIXED = 0.5;

type Health = 'good' | 'mixed' | 'bad' | 'running' | 'none';

// Canceled runs are neither passes nor failures, so they sit outside the rate.
const healthFor = (counts: Partial<Record<Bucket, number>>): Health => {
  const finished = (counts.success ?? 0) + (counts.failure ?? 0);
  if (!finished) {
    return counts.inProgress || counts.queued ? 'running' : 'none';
  }
  const rate = (counts.success ?? 0) / finished;
  return rate >= HEALTH_GOOD ? 'good' : rate >= HEALTH_MIXED ? 'mixed' : 'bad';
};

const HEALTH_FILL: Record<Health, string> = {
  good: Colors.dataVizGreen(),
  mixed: Colors.dataVizYellow(),
  bad: Colors.dataVizRed(),
  running: Colors.dataVizBlue(),
  none: EMPTY_DAY,
};

const HEALTH_TEXT: Record<Health, string> = {
  good: Colors.textGreen(),
  mixed: Colors.textYellow(),
  bad: Colors.textRed(),
  running: Colors.textBlue(),
  none: Colors.textLighter(),
};

export const startOfDay = (daysAgo: number) => {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - daysAgo);
  return d;
};

const RunStatusBlock = () => {
  // Fixed for the life of the page so the query variables stay stable.
  const [historyStart] = useState(() => startOfDay(HISTORY_DAYS - 1));
  const [yesterdayStart] = useState(() => startOfDay(1));

  const historyResult = useQuery<HillpointeRunHistoryQuery, HillpointeRunHistoryQueryVariables>(
    HILLPOINTE_RUN_HISTORY_QUERY,
    {variables: {after: historyStart.getTime() / 1000}},
  );
  useQueryRefreshAtInterval(historyResult, FIFTEEN_SECONDS);
  const rowCountResult = useQuery<HillpointeRowCountQuery, HillpointeRowCountQueryVariables>(
    HILLPOINTE_ROW_COUNT_QUERY,
    {variables: {after: yesterdayStart.getTime() / 1000}},
  );
  useQueryRefreshAtInterval(rowCountResult, FIFTEEN_SECONDS);

  const runs: HistoryRun[] = useMemo(() => {
    const result = historyResult.data?.runsOrError;
    return result?.__typename === 'Runs' ? result.results : [];
  }, [historyResult.data]);

  const days = useMemo(() => {
    const list = Array.from({length: HISTORY_DAYS}, (_, i) => {
      const date = new Date(historyStart);
      date.setDate(historyStart.getDate() + i);
      return {date, counts: {} as Partial<Record<Bucket, number>>, total: 0};
    });
    const byKey = new Map(list.map((d) => [dayKey(d.date), d]));
    runs.forEach((r) => {
      const day = byKey.get(dayKey(new Date(r.creationTime * 1000)));
      if (day) {
        const bucket = bucketFor(r.status);
        day.counts[bucket] = (day.counts[bucket] ?? 0) + 1;
        day.total++;
      }
    });
    return list;
  }, [runs, historyStart]);

  // Same rules as scripts/daily_row_totals.py: sum each step's rows_copied, credited to the
  // day the run started. null means no step recorded a count that day.
  const rowCounts = useMemo(() => {
    const result = rowCountResult.data?.runsOrError;
    const totals: {yesterday: number | null; today: number | null} = {
      yesterday: null,
      today: null,
    };
    const todayStart = startOfDay(0).getTime() / 1000;
    const yesterdayStartSec = yesterdayStart.getTime() / 1000;
    (result?.__typename === 'Runs' ? result.results : []).forEach((run) => {
      if (!run.startTime || run.startTime < yesterdayStartSec) {
        return;
      }
      const day = run.startTime >= todayStart ? 'today' : 'yesterday';
      run.assetMaterializations.forEach((m) =>
        m.metadataEntries.forEach((e) => {
          if (e.__typename === 'IntMetadataEntry' && e.label === ROW_COUNT_LABEL) {
            totals[day] = (totals[day] ?? 0) + Number(e.intRepr);
          }
        }),
      );
    });
    return totals;
  }, [rowCountResult.data, yesterdayStart]);

  const today = days[days.length - 1];
  const todayFinished = today ? (today.counts.success ?? 0) + (today.counts.failure ?? 0) : 0;
  const todayRunning = (today?.total ?? 0) - todayFinished - (today?.counts.canceled ?? 0);
  const todayHealth = healthFor(today?.counts ?? {});
  const week = days
    .slice(-7)
    .reduce(
      (acc, d) => ({total: acc.total + d.total, failed: acc.failed + (d.counts.failure ?? 0)}),
      {total: 0, failed: 0},
    );
  // Runs arrive newest first.
  const lastFailure = runs.find((r) => bucketFor(r.status) === 'failure');

  return (
    <div className={styles.card}>
      <div className={styles.jobHeader}>
        <div className={styles.jobTitle}>
          <span className={styles.dot} style={{background: HEALTH_FILL[todayHealth]}} />
          Pipeline runs
          <Tooltip content="Colour is the share of finished runs that succeeded: green for 80% or more, yellow for 50–79%, red below 50%. Blue: runs still going, none finished yet. Empty: no runs. Row counts add up the rows_copied each step records, by the day its run started; — means no step recorded a count.">
            <Icon name="info" color={Colors.textLighter()} />
          </Tooltip>
        </div>
      </div>
      <div className={styles.statusBody}>
        <div className={styles.statusLeft}>
          <div className={styles.statGrid}>
            <div className={styles.miniTile}>
              <div className={styles.tileLabel}>Row count yesterday</div>
              <div className={styles.jobStatValue}>
                {rowCounts.yesterday?.toLocaleString() ?? '—'}
              </div>
            </div>
            <div className={styles.miniTile}>
              <div className={styles.tileLabel}>Row count today</div>
              <div className={styles.jobStatValue}>{rowCounts.today?.toLocaleString() ?? '—'}</div>
            </div>
            <div className={styles.miniTile}>
              <div className={styles.tileLabel}>Today&apos;s status</div>
              <div className={styles.jobStatValue} style={{color: HEALTH_TEXT[todayHealth]}}>
                {today?.total
                  ? `${today.counts.success ?? 0}/${todayFinished} passed${
                      todayRunning ? `, ${todayRunning} running` : ''
                    }`
                  : 'No runs'}
              </div>
            </div>
            <div className={styles.miniTile}>
              <div className={styles.tileLabel}>Runs, last 7 days</div>
              <div className={styles.jobStatValue}>{week.total}</div>
            </div>
            <div className={styles.miniTile}>
              <div className={styles.tileLabel}>Failed, last 7 days</div>
              <div
                className={styles.jobStatValue}
                style={{color: week.failed ? Colors.textRed() : undefined}}
              >
                {week.failed}
              </div>
            </div>
            <div className={styles.miniTile}>
              <div className={styles.tileLabel}>Last failure</div>
              <div className={styles.jobStatValue}>
                {lastFailure
                  ? new Date(lastFailure.creationTime * 1000).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                    })
                  : 'None'}
              </div>
            </div>
          </div>
        </div>
        <RunMonthCalendar days={days} />
      </div>
    </div>
  );
};

type DayCounts = {date: Date; counts: Partial<Record<Bucket, number>>; total: number};

const WEEKDAY_LETTERS = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

/**
 * A month as a calendar: one dot per day, coloured by that day's health. Arrows
 * step back through the months the loaded history covers, and forward to today.
 */
const RunMonthCalendar = ({days}: {days: DayCounts[]}) => {
  // 0 is the current month, -1 the month before, and so on.
  const [offset, setOffset] = useState(0);
  const byKey = new Map(days.map((d) => [dayKey(d.date), d]));
  const today = startOfDay(0);
  const monthStart = new Date(today.getFullYear(), today.getMonth() + offset, 1);
  const daysInMonth = new Date(monthStart.getFullYear(), monthStart.getMonth() + 1, 0).getDate();
  // Can't go further back than the month holding the oldest loaded day.
  const oldest = days[0]?.date ?? today;
  const canGoBack = monthStart > new Date(oldest.getFullYear(), oldest.getMonth(), 1);
  // Leading blanks so the 1st lands on its weekday, Monday first.
  const lead = (monthStart.getDay() + 6) % 7;
  const cells = [
    ...Array.from({length: lead}, () => null),
    ...Array.from({length: daysInMonth}, (_, i) => {
      const date = new Date(monthStart);
      date.setDate(i + 1);
      return {date, day: byKey.get(dayKey(date)), future: date > today};
    }),
  ];

  return (
    <div className={styles.month}>
      <div className={styles.monthNav}>
        <Button
          icon={<Icon name="chevron_left" />}
          disabled={!canGoBack}
          onClick={() => setOffset(offset - 1)}
          aria-label="Previous month"
        />
        <div className={styles.monthTitle}>
          {monthStart.toLocaleDateString(undefined, {month: 'long', year: 'numeric'})}
        </div>
        <Button
          icon={<Icon name="chevron_right" />}
          disabled={offset === 0}
          onClick={() => setOffset(offset + 1)}
          aria-label="Next month"
        />
      </div>
      <div className={styles.monthGrid}>
        {WEEKDAY_LETTERS.map((letter, i) => (
          <div key={i} className={styles.calHead}>
            {letter}
          </div>
        ))}
        {cells.map((cell, i) => {
          if (!cell) {
            return <div key={`lead-${i}`} />;
          }
          const {date, day, future} = cell;
          const health = future ? 'none' : healthFor(day?.counts ?? {});
          const dot = (
            <div
              className={clsx(styles.monthDot, future && styles.monthFuture)}
              style={{
                background: HEALTH_FILL[health],
                color: health === 'none' ? Colors.textLighter() : Colors.backgroundDefault(),
              }}
            >
              {date.getDate()}
            </div>
          );
          return future ? (
            <span key={date.toISOString()}>{dot}</span>
          ) : (
            <Tooltip
              key={date.toISOString()}
              content={
                <div>
                  <strong>{date.toLocaleDateString()}</strong>:{' '}
                  {day?.total ? `${day.total} runs` : 'No runs'}
                  {BUCKETS.filter((b) => day?.counts[b.key]).map((b) => (
                    <div key={b.key}>
                      {b.label}: {day?.counts[b.key]}
                    </div>
                  ))}
                </div>
              }
            >
              {dot}
            </Tooltip>
          );
        })}
      </div>
    </div>
  );
};

const HOUR = 3600;

const formatHour = (secs: number) =>
  new Date(secs * 1000).toLocaleTimeString(undefined, {hour: 'numeric'});

type TrendMode = 'schedule' | 'replay';
const TREND_MODE_KEY = 'hillpointe-trend-mode';
const TREND_MODES: {id: TrendMode; label: string; sub: string}[] = [
  {id: 'replay', label: 'Replay last night', sub: 'Midnight to noon today, sped up'},
  {id: 'schedule', label: "Tonight's schedule", sub: 'Last night, and what runs next'},
];

/** Success rate gets its own card, placed under Pipeline runs. */
const SuccessRateCard = () => (
  <div className={styles.card}>
    <div className={styles.cardHeader}>
      <div className={styles.cardTitle}>
        Success rate
        <span className={styles.cardSub}>
          {ROLLING_DAYS}-day rolling, last {TREND_DAYS} days
        </span>
      </div>
    </div>
    <SuccessRateTrend />
  </div>
);

/** One card that switches between the replay and today's timeline. */
// The card rotates between its views on its own, for wall screens.
const ROTATE_EVERY_MS = 3 * 60 * 1000;

const TrendCard = ({runs}: {runs: Run[]}) => {
  const [mode, setMode] = useStateWithStorage<TrendMode>(TREND_MODE_KEY, (value) =>
    TREND_MODES.some((m) => m.id === value) ? value : 'replay',
  );
  const current = TREND_MODES.find((m) => m.id === mode) ?? TREND_MODES[0];

  // Advance to the next view every ROTATE_EVERY_MS. Picking a view by hand
  // restarts the timer from that view.
  useEffect(() => {
    const timer = setTimeout(() => {
      const index = TREND_MODES.findIndex((m) => m.id === mode);
      const next = TREND_MODES[(index + 1) % TREND_MODES.length];
      if (next) {
        setMode(next.id);
      }
    }, ROTATE_EVERY_MS);
    return () => clearTimeout(timer);
  }, [mode, setMode]);
  return (
    <div className={clsx(styles.card, styles.cardFlex)}>
      <div className={styles.cardHeader}>
        <div className={styles.cardTitle}>
          {current?.label}
          <span className={styles.cardSub}>{current?.sub}</span>
        </div>
        <ButtonGroup<TrendMode>
          activeItems={new Set([mode])}
          buttons={TREND_MODES.map(({id, label}) => ({id, label}))}
          onClick={setMode}
        />
      </div>
      {mode === 'schedule' ? <ScheduleBoard runs={runs} /> : null}
      {mode === 'replay' ? <ReplayNight runs={runs} /> : null}
    </div>
  );
};

// ---- Tonight's schedule ----------------------------------------------------
// One row per job: how its last run went, and a live countdown to its next
// scheduled run. Jobs without a schedule get an expected time 24h after their
// last run, marked as such.

const DAY = 24 * HOUR;
const LOOKBACK_FOR_ROWS_DAYS = 2;
// When the list is taller than the card it scrolls continuously, this long per job.
const BOARD_SECONDS_PER_ROW = 2.5;
// Scrolling by hand pauses the auto-scroll for this long.
const BOARD_MANUAL_PAUSE_MS = 8000;
// The list rests this long at the top and at the bottom of each pass.
const BOARD_END_REST_MS = 10000;

type BoardRow = {
  job: string;
  status: RunStatus;
  start: number;
  duration: number | null;
  rows: number;
  next: number | null;
  nextIsGuess: boolean;
};

const formatCountdown = (secs: number) => {
  const s = Math.max(0, Math.floor(secs));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const pad = (n: number) => `${n}`.padStart(2, '0');
  return h > 0 ? `${h}h ${pad(m)}m ${pad(sec)}s` : `${m}m ${pad(sec)}s`;
};

const ScheduleBoard = ({runs}: {runs: Run[]}) => {
  const [rowsAfter] = useState(() => startOfDay(LOOKBACK_FOR_ROWS_DAYS - 1).getTime() / 1000);
  const rowResult = useQuery<HillpointeRowCountQuery, HillpointeRowCountQueryVariables>(
    HILLPOINTE_ROW_COUNT_QUERY,
    {variables: {after: rowsAfter}},
  );
  useQueryRefreshAtInterval(rowResult, FIFTEEN_SECONDS);
  const scheduleResult = useQuery<HillpointeSchedulesQuery, HillpointeSchedulesQueryVariables>(
    HILLPOINTE_SCHEDULES_QUERY,
  );
  useQueryRefreshAtInterval(scheduleResult, FIFTEEN_SECONDS);

  // Ticks once a second so the countdowns move.
  const [now, setNow] = useState(() => Date.now() / 1000);
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now() / 1000), 1000);
    return () => clearInterval(timer);
  }, []);

  const rowsByRun = useMemo(() => {
    const map = new Map<string, number>();
    const result = rowResult.data?.runsOrError;
    (result?.__typename === 'Runs' ? result.results : []).forEach((run) => {
      run.assetMaterializations.forEach((m) =>
        m.metadataEntries.forEach((e) => {
          if (e.__typename === 'IntMetadataEntry' && e.label === ROW_COUNT_LABEL) {
            map.set(run.id, (map.get(run.id) ?? 0) + Number(e.intRepr));
          }
        }),
      );
    });
    return map;
  }, [rowResult.data]);

  // Next tick per job from its schedules; the earliest wins.
  const nextByJob = useMemo(() => {
    const map = new Map<string, number>();
    const ws = scheduleResult.data?.workspaceOrError;
    if (ws?.__typename !== 'Workspace') {
      return map;
    }
    ws.locationEntries.forEach((entry) => {
      const loc = entry.locationOrLoadError;
      if (loc?.__typename !== 'RepositoryLocation') {
        return;
      }
      loc.repositories.forEach((repo) =>
        repo.schedules.forEach((sched) => {
          if (sched.scheduleState.status !== InstigationStatus.RUNNING) {
            return;
          }
          const tick = sched.futureTicks.results[0]?.timestamp;
          if (tick) {
            const prev = map.get(sched.pipelineName);
            map.set(sched.pipelineName, prev === undefined ? tick : Math.min(prev, tick));
          }
        }),
      );
    });
    return map;
  }, [scheduleResult.data]);

  const board: BoardRow[] = useMemo(() => {
    const latest = new Map<string, Run>();
    runs.forEach((r) => {
      if (!r.startTime) {
        return;
      }
      const prev = latest.get(r.jobName);
      if (!prev || (prev.startTime ?? 0) < r.startTime) {
        latest.set(r.jobName, r);
      }
    });
    return [...latest.values()]
      .map((r) => {
        const start = r.startTime ?? 0;
        const scheduled = nextByJob.get(r.jobName);
        // No schedule: expect it again a day after it last started, if that is still ahead.
        const guess = start + DAY > now ? start + DAY : null;
        return {
          job: r.jobName,
          status: r.status,
          start,
          duration: durationSec(r.startTime, r.endTime),
          rows: rowsByRun.get(r.runId) ?? 0,
          next: scheduled ?? guess,
          nextIsGuess: scheduled === undefined,
        };
      })
      .sort((a, b) => (a.next ?? Infinity) - (b.next ?? Infinity));
  }, [runs, rowsByRun, nextByJob, now]);

  // The list is a real scroll container, so the wheel and touch work. When the
  // jobs overflow the card a frame loop scrolls it down to the last job, rests,
  // comes back up to the top, rests, and goes again. Hovering or scrolling by hand
  // pauses it for a while.
  const scrollRef = useRef<HTMLDivElement>(null);
  const [scrolling, setScrolling] = useState(false);
  const pausedUntil = useRef(0);
  const hovering = useRef(false);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) {
      return;
    }
    const measure = () => setScrolling(el.scrollHeight > el.clientHeight + 1);
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => observer.disconnect();
  }, [board.length]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || !scrolling) {
      return;
    }
    let frame = 0;
    let last = performance.now();
    // Fractional position: scrollTop itself is rounded to whole pixels, so
    // adding a third of a pixel per frame directly would never move.
    let pos = el.scrollTop;
    let direction = 1;
    pausedUntil.current = Math.max(pausedUntil.current, performance.now() + BOARD_END_REST_MS);
    const tick = (now: number) => {
      const dt = (now - last) / 1000;
      last = now;
      const maxScroll = el.scrollHeight - el.clientHeight;
      // A hand scroll moved the list; carry on from where it was left.
      if (Math.abs(el.scrollTop - Math.round(pos)) > 1) {
        pos = el.scrollTop;
      }
      if (!hovering.current && now > pausedUntil.current) {
        const speed = el.scrollHeight / board.length / BOARD_SECONDS_PER_ROW;
        pos += direction * speed * dt;
        if (pos >= maxScroll) {
          pos = maxScroll;
          direction = -1;
          pausedUntil.current = now + BOARD_END_REST_MS;
        } else if (pos <= 0) {
          pos = 0;
          direction = 1;
          pausedUntil.current = now + BOARD_END_REST_MS;
        }
      }
      el.scrollTop = Math.round(pos);
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [scrolling, board.length]);

  const pauseForManual = () => {
    pausedUntil.current = performance.now() + BOARD_MANUAL_PAUSE_MS;
  };

  if (!board.length) {
    return <div className={styles.muted}>No runs this month yet.</div>;
  }

  const renderRow = (row: BoardRow, key: string) => {
    const running = bucketFor(row.status) === 'inProgress' || bucketFor(row.status) === 'queued';
    return (
      <div key={key} className={styles.boardRow}>
        <span className={styles.boardJob} title={row.job}>
          {row.job}
        </span>
        <span className={styles.boardStatus}>
          <RunStatusTag status={row.status} />
          <span className={styles.muted}>
            <TimeFromNow unixTimestamp={row.start} />
          </span>
        </span>
        <span className={styles.boardNum}>{row.rows ? row.rows.toLocaleString() : '—'}</span>
        <span className={styles.boardNum}>{formatDuration(row.duration)}</span>
        <span className={styles.boardNext}>
          {running ? (
            <span className={styles.boardLive}>running now</span>
          ) : row.next ? (
            <>
              <span className={styles.boardCountdown}>in {formatCountdown(row.next - now)}</span>
              <span className={styles.muted}>
                {new Date(row.next * 1000).toLocaleTimeString(undefined, {
                  hour: 'numeric',
                  minute: '2-digit',
                })}
                {row.nextIsGuess ? ' · expected' : ''}
              </span>
            </>
          ) : (
            <span className={styles.muted}>not scheduled</span>
          )}
        </span>
      </div>
    );
  };

  return (
    <div className={styles.board}>
      <div className={clsx(styles.boardRow, styles.boardHead)}>
        <span>Job</span>
        <span>Last run</span>
        <span className={styles.boardNum}>Rows</span>
        <span className={styles.boardNum}>Took</span>
        <span className={styles.boardNext}>Next run</span>
      </div>
      <div
        ref={scrollRef}
        className={styles.boardScroll}
        onMouseEnter={() => (hovering.current = true)}
        onMouseLeave={() => (hovering.current = false)}
        onWheel={pauseForManual}
        onTouchStart={pauseForManual}
      >
        <div className={styles.boardTrack}>{board.map((row) => renderRow(row, row.job))}</div>
      </div>
    </div>
  );
};

// ---- Replay last night ------------------------------------------------------
// Pipelines run overnight, so a daytime demo has nothing live to show. Replay
// walks a clock through last night's recorded runs in REPLAY_SECONDS, feeding
// the same kind of tiles, bars and feed a live view would. Real data, sped up.

const REPLAY_SECONDS = 45;
const NIGHT_START_HOUR = 0; // midnight today
const NIGHT_END_HOUR = 12; // noon today
const REPLAY_FEED_LINES = 14;

type ReplayRun = {
  runId: string;
  jobName: string;
  status: RunStatus;
  start: number;
  end: number | null;
  rows: number;
};

const nightWindow = () => {
  const start = startOfDay(0);
  start.setHours(NIGHT_START_HOUR, 0, 0, 0);
  const end = startOfDay(0);
  end.setHours(NIGHT_END_HOUR, 0, 0, 0);
  return {start: start.getTime() / 1000, end: end.getTime() / 1000};
};

/** 5,000 -> "5k", 7,500,000 -> "7.5M". */
const formatRows = (n: number) => {
  if (n >= 1e6) {
    const m = n / 1e6;
    return `${Number.isInteger(m) ? m : m.toFixed(1)}M`;
  }
  if (n >= 1e3) {
    return `${Math.round(n / 1e3)}k`;
  }
  return `${n}`;
};

// Bottom of the log axis; hours with fewer rows than this draw as empty.
const LOG_FLOOR = 1_000;

const formatClock = (secs: number) =>
  new Date(secs * 1000).toLocaleTimeString(undefined, {hour: 'numeric', minute: '2-digit'});

const ReplayNight = ({runs}: {runs: Run[]}) => {
  const [window] = useState(nightWindow);
  const span = window.end - window.start;

  const rowResult = useQuery<HillpointeRowCountQuery, HillpointeRowCountQueryVariables>(
    HILLPOINTE_ROW_COUNT_QUERY,
    {variables: {after: window.start}},
  );
  const rowsByRun = useMemo(() => {
    const map = new Map<string, number>();
    const result = rowResult.data?.runsOrError;
    (result?.__typename === 'Runs' ? result.results : []).forEach((run) => {
      run.assetMaterializations.forEach((m) =>
        m.metadataEntries.forEach((e) => {
          if (e.__typename === 'IntMetadataEntry' && e.label === ROW_COUNT_LABEL) {
            map.set(run.id, (map.get(run.id) ?? 0) + Number(e.intRepr));
          }
        }),
      );
    });
    return map;
  }, [rowResult.data]);

  const night: ReplayRun[] = useMemo(
    () =>
      runs
        .filter((r) => r.startTime && r.startTime >= window.start && r.startTime < window.end)
        .map((r) => ({
          runId: r.runId,
          jobName: r.jobName,
          status: r.status,
          start: r.startTime ?? window.start,
          end: r.endTime,
          rows: rowsByRun.get(r.runId) ?? 0,
        }))
        .sort((a, b) => a.start - b.start),
    [runs, rowsByRun, window],
  );

  // Playback clock.
  const [clock, setClock] = useState(window.start);
  const done = clock >= window.end;
  useEffect(() => {
    if (done) {
      return;
    }
    let frame = 0;
    let last = performance.now();
    const tick = (now: number) => {
      const dt = (now - last) / 1000;
      last = now;
      setClock((c) => Math.min(window.end, c + (dt * span) / REPLAY_SECONDS));
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [done, window.end, span]);

  const finished = night.filter((r) => r.end !== null && r.end <= clock);
  const passed = finished.filter((r) => r.status === RunStatus.SUCCESS).length;
  const failedCount = finished.filter((r) => bucketFor(r.status) === 'failure').length;
  const rows = finished.reduce((sum, r) => sum + r.rows, 0);
  const running = night.filter((r) => r.start <= clock && (r.end === null || r.end > clock));
  const current = running[0];

  const hours = Math.round(span / HOUR);
  const bars = Array.from({length: hours}, (_, i) => {
    const from = window.start + i * HOUR;
    const total = finished
      .filter((r) => r.end !== null && r.end >= from && r.end < from + HOUR)
      .reduce((sum, r) => sum + r.rows, 0);
    return {from, total};
  });
  // The axis is fixed for the whole night so bars grow against a steady scale.
  const fullBars = Array.from({length: hours}, (_, i) => {
    const from = window.start + i * HOUR;
    return night
      .filter((r) => r.end !== null && r.end >= from && r.end < from + HOUR)
      .reduce((sum, r) => sum + r.rows, 0);
  });
  // Log axis: one hour can load 20M rows while the rest load 200k, and on a
  // linear scale the small hours vanish. Each gridline is ten times the last.
  const peak = Math.max(...fullBars, LOG_FLOOR * 10);
  const axisTop = 10 ** Math.ceil(Math.log10(peak));
  const decades = Math.round(Math.log10(axisTop / LOG_FLOOR));
  const logHeight = (rows: number) =>
    rows < LOG_FLOOR ? 0 : (Math.log10(rows / LOG_FLOOR) / decades) * 100;
  const ticks = Array.from({length: decades + 1}, (_, i) => LOG_FLOOR * 10 ** i);

  const feed = night
    .flatMap((r) => [
      {time: r.start, text: `${r.jobName} started`, tone: styles.feedStart},
      ...(r.end !== null
        ? [
            r.status === RunStatus.SUCCESS
              ? {
                  time: r.end,
                  text: `${r.jobName} succeeded${r.rows ? ` · ${r.rows.toLocaleString()} rows` : ''}`,
                  tone: styles.feedOk,
                }
              : {time: r.end, text: `${r.jobName} ${r.status.toLowerCase()}`, tone: styles.feedBad},
          ]
        : []),
    ])
    .filter((e) => e.time <= clock)
    .sort((a, b) => b.time - a.time)
    .slice(0, REPLAY_FEED_LINES);

  if (!night.length) {
    return <div className={styles.muted}>No runs between midnight and noon today.</div>;
  }

  return (
    <>
      <div className={styles.replayHead}>
        <span className={styles.replayClock}>{formatClock(clock)}</span>
        <span className={styles.replayTag}>{done ? 'Night complete' : 'Replaying last night'}</span>
      </div>
      <div className={styles.replayProgress}>
        <div style={{width: `${((clock - window.start) / span) * 100}%`}} />
      </div>
      <div className={styles.replayChart}>
        <div className={styles.cardSub}>Rows loaded per hour · log scale</div>
        <div className={styles.rpPlot}>
          {ticks.map((t) => (
            <div key={t} className={styles.rpTick} style={{bottom: `${logHeight(t)}%`}}>
              <span>{formatRows(t)}</span>
            </div>
          ))}
          <div className={styles.rpChart}>
            {bars.map((b, i) => (
              <div
                key={b.from}
                className={styles.rpCol}
                title={`${formatHour(b.from)}: ${b.total.toLocaleString()} rows`}
              >
                <div className={styles.rpBar} style={{height: `${logHeight(b.total)}%`}} />
                <span className={styles.rpLabel}>{i % 2 === 0 ? formatHour(b.from) : ''}</span>
              </div>
            ))}
          </div>
        </div>
        <div className={styles.rpAxisTitle}>Time rows were inserted</div>
      </div>
      <div className={styles.replayBottom}>
        <div className={styles.replayFeed}>
          <div className={styles.cardSub}>Activity</div>
          <div className={styles.feed}>
            {feed.map((e) => (
              <div key={`${e.time}-${e.text}`} className={styles.feedLine}>
                <span className={styles.feedTime}>{formatClock(e.time)}</span>
                <span className={e.tone}>{e.text}</span>
              </div>
            ))}
          </div>
        </div>
        <div className={styles.replayTiles}>
          <div className={styles.miniTile}>
            <div className={styles.tileLabel}>Runs finished</div>
            <div className={styles.jobStatValue}>
              <CountUp value={finished.length} />
            </div>
          </div>
          <div className={styles.miniTile}>
            <div className={styles.tileLabel}>Success rate</div>
            <div className={styles.jobStatValue}>
              {finished.length ? (
                <CountUp value={(passed / finished.length) * 100} format={percent} />
              ) : (
                '—'
              )}
            </div>
            <div className={styles.tileSub}>
              {passed} passed · {failedCount} failed
            </div>
          </div>
          <div className={styles.miniTile}>
            <div className={styles.tileLabel}>Rows loaded</div>
            <div className={styles.jobStatValue}>
              <CountUp value={rows} />
            </div>
          </div>
          <div className={styles.miniTile}>
            <div className={styles.tileLabel}>Running now</div>
            <div className={styles.jobStatValue}>{current ? current.jobName : 'idle'}</div>
            <div className={styles.stepTrack}>
              {current ? (
                <div
                  className={styles.stepBar}
                  style={{
                    width: `${Math.min(
                      100,
                      ((clock - current.start) / ((current.end ?? window.end) - current.start)) *
                        100,
                    )}%`,
                    background: Colors.accentBlue(),
                  }}
                />
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

const TREND_HEIGHT = 160;

/**
 * Rolling success rate over the last TREND_DAYS days, as a line. Each point is
 * the share of finished runs that succeeded in the ROLLING_DAYS days ending on
 * that day, so one bad run nudges the line rather than dropping it to zero.
 */
const SuccessRateTrend = () => {
  // Same variables as RunStatusBlock's history query, so Apollo serves it from cache.
  const [historyStart] = useState(() => startOfDay(HISTORY_DAYS - 1));
  const queryResult = useQuery<HillpointeRunHistoryQuery, HillpointeRunHistoryQueryVariables>(
    HILLPOINTE_RUN_HISTORY_QUERY,
    {variables: {after: historyStart.getTime() / 1000}},
  );
  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const days = useMemo(() => {
    const result = queryResult.data?.runsOrError;
    const runs = result?.__typename === 'Runs' ? result.results : [];
    // Daily counts reach back an extra window so the first point has a full one.
    const span = TREND_DAYS + ROLLING_DAYS - 1;
    const daily = Array.from({length: span}, (_, i) => ({
      date: startOfDay(span - 1 - i),
      succeeded: 0,
      finished: 0,
    }));
    const byKey = new Map(daily.map((d) => [dayKey(d.date), d]));
    runs.forEach((r) => {
      const day = byKey.get(dayKey(new Date(r.creationTime * 1000)));
      const bucket = bucketFor(r.status);
      if (day && (bucket === 'success' || bucket === 'failure')) {
        day.finished++;
        day.succeeded += bucket === 'success' ? 1 : 0;
      }
    });
    return daily.slice(ROLLING_DAYS - 1).map((d, i) => {
      const window = daily.slice(i, i + ROLLING_DAYS);
      const succeeded = window.reduce((sum, w) => sum + w.succeeded, 0);
      const finished = window.reduce((sum, w) => sum + w.finished, 0);
      return {date: d.date, succeeded, finished, rate: finished ? succeeded / finished : null};
    });
  }, [queryResult.data]);

  const latest = days[days.length - 1];
  const pct = (rate: number | null) => (rate === null ? '—' : `${Math.round(rate * 100)}%`);

  // Points sit at column centres; a window with no finished runs breaks the line.
  const step = 100 / TREND_DAYS;
  const x = (i: number) => (i + 0.5) * step;
  const y = (rate: number) => TREND_HEIGHT - rate * TREND_HEIGHT;
  const path = days
    .map((d, i) => (d.rate === null ? '' : `${x(i)},${y(d.rate)}`))
    .reduce((acc, point, i, all) => {
      if (!point) {
        return acc;
      }
      const prev = i > 0 ? all[i - 1] : '';
      return `${acc}${prev ? 'L' : 'M'}${point} `;
    }, '');

  return (
    <>
      <Box flex={{alignItems: 'baseline', gap: 12}}>
        <div className={styles.tileValue}>{pct(latest?.rate ?? null)}</div>
        <div className={styles.tileSub}>
          Last {ROLLING_DAYS} days
          {latest?.finished ? ` · ${latest.succeeded} of ${latest.finished} runs succeeded` : ''}
        </div>
      </Box>
      <div className={styles.tileSub}>
        Each point is the share of runs that succeeded in the {ROLLING_DAYS} days ending on that
        day, so one bad run nudges the line instead of dropping it to zero.
      </div>
      <div className={styles.plot}>
        <div className={styles.gridline}>
          <span className={styles.gridLabel}>100%</span>
        </div>
        <div className={styles.gridline} style={{top: '50%'}}>
          <span className={styles.gridLabel}>50%</span>
        </div>
        <svg
          className={styles.trendSvg}
          viewBox={`0 0 100 ${TREND_HEIGHT}`}
          preserveAspectRatio="none"
        >
          <path
            d={path}
            fill="none"
            stroke={Colors.dataVizGreen()}
            strokeWidth={2}
            vectorEffect="non-scaling-stroke"
          />
        </svg>
        {days.map((day) => (
          <Tooltip
            key={day.date.toISOString()}
            content={
              <div>
                <strong>{day.date.toLocaleDateString()}</strong>:{' '}
                {day.finished
                  ? `${pct(day.rate)} · ${day.succeeded} of ${day.finished} runs succeeded in the ${ROLLING_DAYS} days ending here`
                  : `No finished runs in the ${ROLLING_DAYS} days ending here`}
              </div>
            }
          >
            <div className={styles.column}>
              {day.rate !== null ? (
                <span
                  className={styles.point}
                  style={{
                    top: `${(1 - day.rate) * 100}%`,
                    background: Colors.dataVizGreen(),
                  }}
                />
              ) : null}
            </div>
          </Tooltip>
        ))}
      </div>
      <div className={styles.xLabels}>
        {days.map((day, i) => (
          <div key={day.date.toISOString()} className={styles.xLabel}>
            {(TREND_DAYS - 1 - i) % 7 === 0
              ? day.date.toLocaleDateString(undefined, {month: 'short', day: 'numeric'})
              : ''}
          </div>
        ))}
      </div>
    </>
  );
};

const RunBreakdown = ({
  run,
  stats,
  isLatest,
  onShowLatest,
}: {
  run: Run;
  stats: RunStats | null;
  isLatest: boolean;
  onShowLatest: () => void;
}) => {
  const {data, loading} = useQuery<
    HillpointeRunStepStatsQuery,
    HillpointeRunStepStatsQueryVariables
  >(HILLPOINTE_RUN_STEP_STATS_QUERY, {variables: {runId: run.runId}});

  const steps = useMemo(() => {
    const stats = data?.runOrError.__typename === 'Run' ? data.runOrError.stepStats : [];
    return stats
      .map((s) => ({...s, duration: durationSec(s.startTime, s.endTime)}))
      .sort((a, b) => (b.duration ?? 0) - (a.duration ?? 0));
  }, [data]);
  const max = Math.max(1, ...steps.map((s) => s.duration ?? 0));
  const stepStatuses = Object.entries(STEP_COLOR).map(([status, color]) => ({
    label: status.charAt(0) + status.slice(1).toLowerCase().replace('_', ' '),
    color,
  }));

  return (
    <div className={styles.card}>
      <Box flex={{alignItems: 'center', gap: 12, wrap: 'wrap'}}>
        <div className={styles.cardTitle}>
          Run breakdown
          <span className={styles.cardSub}>
            <Link to={`/runs/${run.runId}`}>{run.runId.slice(0, 8)}</Link> · {run.jobName}
          </span>
        </div>
        <RunStatusTag status={run.status} />
        {isLatest ? (
          <Tag icon="history">Latest run</Tag>
        ) : (
          <>
            <Tag icon="history">Selected run</Tag>
            <Button onClick={onShowLatest}>Show latest run</Button>
          </>
        )}
      </Box>
      <div className={styles.tiles}>
        <Tile label="Duration" value={formatDuration(durationSec(run.startTime, run.endTime))} />
        <Tile label="Steps succeeded" value={`${stats?.stepsSucceeded ?? '—'}`} />
        <Tile label="Steps failed" value={`${stats?.stepsFailed ?? '—'}`} />
        <Tile label="Materializations" value={`${stats?.materializations ?? '—'}`} />
      </div>
      <div className={styles.cardTitle}>
        Step durations<span className={styles.cardSub}>Longest first</span>
      </div>
      <Legend items={stepStatuses} />
      {loading && !data ? (
        <Spinner purpose="section" />
      ) : steps.length ? (
        <div className={styles.stepRows}>
          {steps.map((step) => (
            <div key={step.stepKey} className={styles.stepRow}>
              <div className={styles.stepName} title={step.stepKey}>
                {step.stepKey}
              </div>
              <div className={styles.stepTrack}>
                <div
                  className={styles.stepBar}
                  style={{
                    width: `${((step.duration ?? 0) / max) * 100}%`,
                    background: step.status ? STEP_COLOR[step.status] : Colors.dataVizGray(),
                  }}
                />
              </div>
              <div className={styles.stepValue}>{formatDuration(step.duration)}</div>
            </div>
          ))}
        </div>
      ) : (
        <div className={styles.muted}>No steps have started for this run.</div>
      )}
    </div>
  );
};

interface SelectableProps {
  runs: Run[];
  statsByRun: StatsByRun;
  selectedRunId: string | null;
  onSelect: (runId: string) => void;
}

const RunsTable = ({runs, statsByRun, selectedRunId, onSelect}: SelectableProps) => (
  <div className={styles.card}>
    <div className={styles.cardTitle}>
      Runs this month
      <span className={styles.cardSub}>
        Latest {Math.min(TABLE_ROWS, runs.length)} of {runs.length} · click a row to inspect it
        above
      </span>
    </div>
    <div className={styles.tableWrap}>
      <Table>
        <thead>
          <tr>
            <th>Run</th>
            <th>Job</th>
            <th>Status</th>
            <th>Created</th>
            <th>Duration</th>
            <th>Steps ok / failed</th>
            <th>Materializations</th>
          </tr>
        </thead>
        <tbody>
          {runs.slice(0, TABLE_ROWS).map((run) => {
            const stats = statsByRun?.get(run.runId) ?? null;
            return (
              <tr
                key={run.runId}
                className={clsx(styles.runRow, run.runId === selectedRunId && styles.selected)}
                onClick={() => onSelect(run.runId)}
              >
                <td>
                  <Link to={`/runs/${run.runId}`} onClick={(e) => e.stopPropagation()}>
                    {run.runId.slice(0, 8)}
                  </Link>
                </td>
                <td>{run.jobName}</td>
                <td>
                  <RunStatusTag status={run.status} />
                </td>
                <td>{new Date(run.creationTime * 1000).toLocaleString()}</td>
                <td>{formatDuration(durationSec(run.startTime, run.endTime))}</td>
                <td>
                  {stats
                    ? `${stats.stepsSucceeded} / ${stats.stepsFailed}`
                    : statsByRun
                      ? '—'
                      : '…'}
                </td>
                <td>{stats ? stats.materializations : statsByRun ? '—' : '…'}</td>
              </tr>
            );
          })}
        </tbody>
      </Table>
    </div>
  </div>
);

export const HILLPOINTE_RUN_METRICS_QUERY = gql`
  query HillpointeRunMetricsQuery($after: Float!, $limit: Int!) {
    runsOrError(filter: {createdAfter: $after}, limit: $limit) {
      ... on Runs {
        results {
          id
          runId
          jobName
          status
          creationTime
          startTime
          endTime
        }
      }
    }
  }
`;

// Per-run stats come from the event log and are slow for a whole month of
// runs, so they load separately and fill in after the page has rendered.
export const HILLPOINTE_RUN_STATS_QUERY = gql`
  query HillpointeRunStatsQuery($after: Float!, $limit: Int!) {
    runsOrError(filter: {createdAfter: $after}, limit: $limit) {
      ... on Runs {
        results {
          id
          runId
          stats {
            ... on RunStatsSnapshot {
              id
              stepsSucceeded
              stepsFailed
              materializations
            }
          }
        }
      }
    }
  }
`;

export const HILLPOINTE_RUN_HISTORY_QUERY = gql`
  query HillpointeRunHistoryQuery($after: Float!) {
    runsOrError(filter: {createdAfter: $after}, limit: 5000) {
      ... on Runs {
        results {
          id
          status
          creationTime
        }
      }
    }
  }
`;

export const HILLPOINTE_ROW_COUNT_QUERY = gql`
  query HillpointeRowCountQuery($after: Float!) {
    runsOrError(filter: {createdAfter: $after}, limit: 1000) {
      ... on Runs {
        results {
          id
          startTime
          assetMaterializations {
            metadataEntries {
              label
              ... on IntMetadataEntry {
                intRepr
              }
            }
          }
        }
      }
    }
  }
`;

export const HILLPOINTE_SCHEDULES_QUERY = gql`
  query HillpointeSchedulesQuery {
    workspaceOrError {
      ... on Workspace {
        id
        locationEntries {
          id
          locationOrLoadError {
            ... on RepositoryLocation {
              id
              repositories {
                id
                schedules {
                  id
                  pipelineName
                  scheduleState {
                    id
                    status
                  }
                  futureTicks(limit: 1) {
                    results {
                      timestamp
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
`;

export const HILLPOINTE_RUN_STEP_STATS_QUERY = gql`
  query HillpointeRunStepStatsQuery($runId: ID!) {
    runOrError(runId: $runId) {
      ... on Run {
        id
        stepStats {
          stepKey
          status
          startTime
          endTime
        }
      }
    }
  }
`;

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default HillpointeRoot;
