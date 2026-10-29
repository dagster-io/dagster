import {
  Box,
  Button,
  Colors,
  Icon,
  NonIdealState,
  Spinner,
  Tooltip,
} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {useMemo, useState} from 'react';
import {Link, useParams} from 'react-router-dom';

import {gql, useQuery} from '../apollo-client';
import {durationSec, formatDuration, startOfDay} from './HillpointeRoot';
import styles from './css/HillpointeRoot.module.css';
import {
  HillpointeJobLocationsQuery,
  HillpointeJobLocationsQueryVariables,
  HillpointeJobRunStatsQuery,
  HillpointeJobRunStatsQueryVariables,
  HillpointeJobTimingsQuery,
  HillpointeJobTimingsQueryVariables,
} from './types/JobTimingsRoot.types';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {RunStatus} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {useStateWithStorage} from '../hooks/useStateWithStorage';
import {RunStatusTag} from '../runs/RunStatusTag';

// How far back the page looks for runs of each job.
const TIMINGS_DAYS = 90;
// Runs compared for the trend tile: the newest few against the few before them.
const TREND_WINDOW = 5;
const PLOT_HEIGHT = 200;
// A run with fewer than this share of the job's assets is a partial run.
const PARTIAL_RUN_FRACTION = 0.5;
// A failure that died this quickly never did real work; it is left off the chart.
const IMMEDIATE_FAILURE_SECS = 120;
const JOBS_PANEL_KEY = 'hillpointe-timings-jobs-open';

type TimedRun = Extract<
  HillpointeJobTimingsQuery['runsOrError'],
  {__typename: 'Runs'}
>['results'][number];

type Point = {run: TimedRun; start: number; seconds: number};

/**
 * Whether a run belongs on the chart: successes always, failures only if they
 * ran long enough to be interesting, canceled runs never.
 */
const isPlottable = (r: TimedRun) => {
  if (!r.startTime || !r.endTime) {
    return false;
  }
  if (r.status === RunStatus.SUCCESS) {
    return true;
  }
  if (r.status === RunStatus.FAILURE) {
    return (durationSec(r.startTime, r.endTime) ?? 0) >= IMMEDIATE_FAILURE_SECS;
  }
  return false;
};

/** Runs of one job for the chart, oldest first, with durations. */
const pointsFor = (runs: TimedRun[], job: string, partial: Set<string>): Point[] =>
  runs
    .filter((r) => r.pipelineName === job && isPlottable(r) && !partial.has(r.runId))
    .map((r) => ({
      run: r,
      start: r.startTime ?? 0,
      seconds: durationSec(r.startTime, r.endTime) ?? 0,
    }))
    .sort((a, b) => a.start - b.start);

const average = (values: number[]) =>
  values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;

const pointColor = (status: RunStatus) =>
  status === RunStatus.SUCCESS ? Colors.dataVizGreen() : Colors.dataVizRed();

export const JobTimingsRoot = () => {
  useTrackPageView();
  useDocumentTitle('Job timings');
  const {jobName} = useParams<{jobName?: string}>();

  const [after] = useState(() => startOfDay(TIMINGS_DAYS - 1).getTime() / 1000);
  const queryResult = useQuery<HillpointeJobTimingsQuery, HillpointeJobTimingsQueryVariables>(
    HILLPOINTE_JOB_TIMINGS_QUERY,
    {variables: {after}},
  );
  const refreshState = useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);
  // Ad hoc asset materializations run under Dagster's hidden __ASSET_JOB; they
  // are not one of our pipelines, so they are left out.
  const runs = useMemo(() => {
    const result = queryResult.data?.runsOrError;
    const all = result?.__typename === 'Runs' ? result.results : [];
    return all.filter((r) => !isHiddenAssetGroupJob(r.pipelineName));
  }, [queryResult.data]);

  // Which code location (live, testing, ...) defines each job today. Runs
  // remember the location name they ran under, which goes stale when a
  // location is renamed, so the current workspace is the source of truth.
  const locationsResult = useQuery<
    HillpointeJobLocationsQuery,
    HillpointeJobLocationsQueryVariables
  >(HILLPOINTE_JOB_LOCATIONS_QUERY);
  const {locationOrder, locationOf} = useMemo(() => {
    const order: string[] = [];
    const of = new Map<string, string>();
    const result = locationsResult.data?.repositoriesOrError;
    if (result?.__typename === 'RepositoryConnection') {
      result.nodes.forEach((repo) => {
        if (!order.includes(repo.location.name)) {
          order.push(repo.location.name);
        }
        repo.pipelines.forEach((p) => {
          if (!of.has(p.name)) {
            of.set(p.name, repo.location.name);
          }
        });
      });
    }
    return {locationOrder: order, locationOf: of};
  }, [locationsResult.data]);

  // Jobs grouped by code location in workspace order, each group ordered by
  // its most recent run, with an average for the picker. Jobs no location
  // defines any more are grouped at the end.
  const jobs = useMemo(() => {
    const byJob = new Map<string, {latest: number; durations: number[]}>();
    runs.forEach((r) => {
      const entry = byJob.get(r.pipelineName) ?? {latest: 0, durations: []};
      entry.latest = Math.max(entry.latest, r.startTime ?? 0);
      const seconds = durationSec(r.startTime, r.endTime);
      if (seconds !== null && r.endTime && r.status === RunStatus.SUCCESS) {
        entry.durations.push(seconds);
      }
      byJob.set(r.pipelineName, entry);
    });
    return [...byJob.entries()]
      .map(([name, {latest, durations}]) => ({
        name,
        location: locationOf.get(name) ?? '',
        latest,
        avg: average(durations),
        count: durations.length,
      }))
      .sort((a, b) => b.latest - a.latest);
  }, [runs, locationOf]);
  const locations = useMemo(
    () => [...locationOrder, ''].filter((loc) => jobs.some((j) => j.location === loc)),
    [jobs, locationOrder],
  );

  const selected = jobName ?? jobs[0]?.name ?? null;
  // The job list can be tucked away to give the chart the full width.
  const [jobsOpen, setJobsOpen] = useStateWithStorage<boolean>(JOBS_PANEL_KEY, (value) =>
    typeof value === 'boolean' ? value : true,
  );
  // A run that materialised well under half the assets of the job's biggest
  // successful run was a partial run (someone picked one or two assets), so it
  // is left out. Half, not "fewer", so a full run with one asset more or less
  // than usual still counts.
  const statsResult = useQuery<HillpointeJobRunStatsQuery, HillpointeJobRunStatsQueryVariables>(
    HILLPOINTE_JOB_RUN_STATS_QUERY,
    {variables: {job: selected ?? ''}, skip: !selected},
  );
  const partial = useMemo(() => {
    const result = statsResult.data?.runsOrError;
    const set = new Set<string>();
    if (result?.__typename !== 'Runs') {
      return set;
    }
    const counts = new Map<string, number>();
    result.results.forEach((r) => {
      if (r.stats.__typename === 'RunStatsSnapshot') {
        counts.set(r.runId, r.stats.materializations);
      }
    });
    const full = Math.max(
      0,
      ...result.results
        .filter((r) => r.status === RunStatus.SUCCESS)
        .map((r) => counts.get(r.runId) ?? 0),
    );
    counts.forEach((count, runId) => {
      if (full > 1 && count < full * PARTIAL_RUN_FRACTION) {
        set.add(runId);
      }
    });
    return set;
  }, [statsResult.data]);

  const points = useMemo(
    () => (selected ? pointsFor(runs, selected, partial) : []),
    [runs, selected, partial],
  );
  const partialCount = useMemo(
    () => runs.filter((r) => r.pipelineName === selected && partial.has(r.runId)).length,
    [runs, selected, partial],
  );

  if (queryResult.loading && !runs.length) {
    return (
      <Box flex={{justifyContent: 'center'}} padding={64}>
        <Spinner purpose="page" />
      </Box>
    );
  }

  return (
    <div className={styles.page}>
      <Box flex={{justifyContent: 'space-between', alignItems: 'center'}}>
        <div className={styles.cardTitle}>
          Job timings
          <span className={styles.cardSub}>How long each run took, last {TIMINGS_DAYS} days</span>
        </div>
        <Box flex={{alignItems: 'center', gap: 12}}>
          <Button
            icon={<Icon name={jobsOpen ? 'panel_show_right' : 'panel_show_left'} />}
            onClick={() => setJobsOpen((open) => !open)}
          >
            {jobsOpen ? 'Hide jobs' : 'Show jobs'}
          </Button>
          <QueryRefreshCountdown refreshState={refreshState} />
        </Box>
      </Box>
      <div className={clsx(styles.timingsGrid, !jobsOpen && styles.timingsGridSolo)}>
        <div className={clsx(styles.card, !jobsOpen && styles.hidden)}>
          <div className={styles.cardTitle}>Jobs</div>
          <div className={styles.jobList}>
            {locations.map((location) => (
              <div key={location}>
                <div className={styles.jobGroup}>{location || 'No longer defined'}</div>
                {jobs
                  .filter((job) => job.location === location)
                  .map((job) => (
                    <Link
                      key={job.name}
                      to={`/hillpointe/timings/${encodeURIComponent(job.name)}`}
                      className={clsx(
                        styles.jobItem,
                        job.name === selected && styles.jobItemActive,
                      )}
                    >
                      <span className={styles.jobItemName} title={job.name}>
                        {job.name}
                      </span>
                      <span className={styles.jobItemMeta}>
                        {job.avg === null ? '—' : formatDuration(job.avg)} avg · {job.count} runs
                      </span>
                    </Link>
                  ))}
              </div>
            ))}
            {!jobs.length ? (
              <div className={styles.muted}>No runs in the last {TIMINGS_DAYS} days.</div>
            ) : null}
          </div>
        </div>
        {selected ? (
          <JobTimings
            job={selected}
            points={points}
            partialCount={partialCount}
            checkingPartial={statsResult.loading && !statsResult.data}
          />
        ) : null}
      </div>
    </div>
  );
};

const JobTimings = ({
  job,
  points,
  partialCount,
  checkingPartial,
}: {
  job: string;
  points: Point[];
  partialCount: number;
  checkingPartial: boolean;
}) => {
  // Only successful runs feed the numbers; failures on the chart are context.
  const good = points.filter((p) => p.run.status === RunStatus.SUCCESS);
  const seconds = good.map((p) => p.seconds);
  const avg = average(seconds);
  const fastest = good.length ? good.reduce((a, b) => (b.seconds < a.seconds ? b : a)) : null;
  const slowest = good.length ? good.reduce((a, b) => (b.seconds > a.seconds ? b : a)) : null;
  const last = good[good.length - 1] ?? null;
  const previous = good[good.length - 2] ?? null;

  // Trend: the newest TREND_WINDOW runs against the TREND_WINDOW before them.
  const recent = average(seconds.slice(-TREND_WINDOW));
  const before = average(seconds.slice(-2 * TREND_WINDOW, -TREND_WINDOW));
  const trend =
    recent !== null && before !== null && before > 0 ? (recent - before) / before : null;

  const top = Math.max(1, ...seconds);
  const x = (i: number) => (i + 0.5) * (100 / Math.max(1, points.length));
  const y = (s: number) => PLOT_HEIGHT - (s / top) * PLOT_HEIGHT;
  const path = points.map((p, i) => `${i ? 'L' : 'M'}${x(i)},${y(p.seconds)}`).join(' ');

  if (!points.length) {
    return (
      <div className={styles.card}>
        <NonIdealState
          icon="timer"
          title="No finished runs"
          description={`${job} has no finished runs in the last ${TIMINGS_DAYS} days.`}
        />
      </div>
    );
  }

  return (
    <div className={styles.timingsMain}>
      <div className={styles.tiles}>
        <div className={styles.tile}>
          <div className={styles.tileLabel}>Last run</div>
          <div className={styles.tileValue}>{formatDuration(last?.seconds ?? null)}</div>
          <div className={styles.tileSub}>
            {last && previous ? <Delta from={previous.seconds} to={last.seconds} /> : 'first run'}
          </div>
        </div>
        <div className={styles.tile}>
          <div className={styles.tileLabel}>Average</div>
          <div className={styles.tileValue}>{formatDuration(avg)}</div>
          <div className={styles.tileSub}>{good.length} successful runs</div>
        </div>
        <div className={styles.tile}>
          <div className={styles.tileLabel}>Fastest</div>
          <div className={styles.tileValue}>{formatDuration(fastest?.seconds ?? null)}</div>
          <div className={styles.tileSub}>{fastest ? dateLabel(fastest.start) : ''}</div>
        </div>
        <div className={styles.tile}>
          <div className={styles.tileLabel}>Slowest</div>
          <div className={styles.tileValue}>{formatDuration(slowest?.seconds ?? null)}</div>
          <div className={styles.tileSub}>{slowest ? dateLabel(slowest.start) : ''}</div>
        </div>
        <div className={styles.tile}>
          <div className={styles.tileLabel}>Trend</div>
          <div className={styles.tileValue}>
            {trend === null ? '—' : <Delta from={before ?? 0} to={recent ?? 0} big />}
          </div>
          <div className={styles.tileSub}>
            Last {TREND_WINDOW} runs vs the {TREND_WINDOW} before
          </div>
        </div>
      </div>

      <div className={styles.card}>
        <div className={styles.cardTitle}>
          {job}
          <span className={styles.cardSub}>
            Successful runs, oldest to newest. Canceled, quickly failed and partial runs are left
            out; longer failures show in red but do not count toward the average.
            {checkingPartial
              ? ' Checking which runs were partial…'
              : partialCount
                ? ` ${partialCount} partial ${partialCount === 1 ? 'run' : 'runs'} left out.`
                : ''}
          </span>
        </div>
        <div className={styles.plot} style={{height: PLOT_HEIGHT}}>
          <div className={styles.gridline}>
            <span className={styles.gridLabel}>{formatDuration(top)}</span>
          </div>
          <div className={styles.gridline} style={{top: '50%'}}>
            <span className={styles.gridLabel}>{formatDuration(top / 2)}</span>
          </div>
          {avg !== null ? (
            <div
              className={clsx(styles.gridline, styles.avgLine)}
              style={{top: `${(1 - avg / top) * 100}%`}}
            >
              <span className={styles.avgLabel}>avg {formatDuration(avg)}</span>
            </div>
          ) : null}
          <svg
            className={styles.trendSvg}
            viewBox={`0 0 100 ${PLOT_HEIGHT}`}
            preserveAspectRatio="none"
          >
            <path
              d={path}
              fill="none"
              stroke={Colors.dataVizBlue()}
              strokeWidth={2}
              vectorEffect="non-scaling-stroke"
            />
          </svg>
          {points.map((p) => (
            <Tooltip
              key={p.run.runId}
              content={
                <div>
                  <strong>{new Date(p.start * 1000).toLocaleString()}</strong>
                  <div>
                    {formatDuration(p.seconds)} · {p.run.status}
                    {avg !== null ? (
                      <>
                        {' · '}
                        <Delta from={avg} to={p.seconds} label="vs avg" />
                      </>
                    ) : null}
                  </div>
                </div>
              }
            >
              <Link to={`/runs/${p.run.runId}`} className={styles.column}>
                <span
                  className={styles.point}
                  style={{
                    top: `${(1 - p.seconds / top) * 100}%`,
                    background: pointColor(p.run.status),
                  }}
                />
              </Link>
            </Tooltip>
          ))}
        </div>
        <div className={styles.xLabels}>
          {points.map((p, i) => (
            <div key={p.run.runId} className={styles.xLabel}>
              {i === 0 || i === points.length - 1 || i % Math.ceil(points.length / 6) === 0
                ? new Date(p.start * 1000).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                  })
                : ''}
            </div>
          ))}
        </div>
      </div>

      <div className={styles.card}>
        <div className={styles.cardTitle}>
          Runs
          <span className={styles.cardSub}>Newest first</span>
        </div>
        <div className={styles.tableWrap}>
          <table className={styles.timingsTable}>
            <thead>
              <tr>
                <th>Started</th>
                <th>Status</th>
                <th className={styles.boardNum}>Duration</th>
                <th className={styles.boardNum}>vs previous</th>
                <th className={styles.boardNum}>vs average</th>
              </tr>
            </thead>
            <tbody>
              {[...points].reverse().map((p, i, all) => {
                const prev = all[i + 1];
                return (
                  <tr key={p.run.runId}>
                    <td>
                      <Link to={`/runs/${p.run.runId}`}>
                        {new Date(p.start * 1000).toLocaleString()}
                      </Link>
                    </td>
                    <td>
                      <RunStatusTag status={p.run.status} />
                    </td>
                    <td className={styles.boardNum}>{formatDuration(p.seconds)}</td>
                    <td className={styles.boardNum}>
                      {prev ? <Delta from={prev.seconds} to={p.seconds} /> : '—'}
                    </td>
                    <td className={styles.boardNum}>
                      {avg !== null ? <Delta from={avg} to={p.seconds} /> : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const dateLabel = (secs: number) =>
  new Date(secs * 1000).toLocaleDateString(undefined, {month: 'short', day: 'numeric'});

/** "12% faster" in green or "8% slower" in red, comparing a run to a baseline. */
const Delta = ({
  from,
  to,
  big,
  label,
}: {
  from: number;
  to: number;
  big?: boolean;
  label?: string;
}) => {
  if (!from) {
    return <span>—</span>;
  }
  const pct = Math.round(((to - from) / from) * 100);
  if (pct === 0) {
    return (
      <span className={clsx(styles.deltaSame, big && styles.deltaBig)}>
        same{label ? ` ${label}` : ''}
      </span>
    );
  }
  const slower = pct > 0;
  return (
    <span
      className={clsx(slower ? styles.deltaSlower : styles.deltaFaster, big && styles.deltaBig)}
    >
      {Math.abs(pct)}% {slower ? 'slower' : 'faster'}
      {label ? ` ${label}` : ''}
    </span>
  );
};

export const HILLPOINTE_JOB_TIMINGS_QUERY = gql`
  query HillpointeJobTimingsQuery($after: Float!) {
    runsOrError(filter: {createdAfter: $after}, limit: 5000) {
      ... on Runs {
        results {
          id
          runId
          pipelineName
          status
          startTime
          endTime
        }
      }
    }
  }
`;

export const HILLPOINTE_JOB_LOCATIONS_QUERY = gql`
  query HillpointeJobLocationsQuery {
    repositoriesOrError {
      ... on RepositoryConnection {
        nodes {
          id
          location {
            id
            name
          }
          pipelines {
            id
            name
          }
        }
      }
    }
  }
`;

// Materialization counts for one job's runs, used to spot partial runs. Run
// stats come from the event log, so this is asked only for the selected job.
export const HILLPOINTE_JOB_RUN_STATS_QUERY = gql`
  query HillpointeJobRunStatsQuery($job: String!) {
    runsOrError(filter: {pipelineName: $job}, limit: 500) {
      ... on Runs {
        results {
          id
          runId
          status
          stats {
            ... on RunStatsSnapshot {
              id
              materializations
            }
          }
        }
      }
    }
  }
`;

// eslint-disable-next-line import/no-default-export
export default JobTimingsRoot;
