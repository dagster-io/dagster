import {Box, Colors, NonIdealState, Spinner, Tooltip} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {useMemo, useState} from 'react';
import {Link, useParams} from 'react-router-dom';

import {gql, useQuery} from '../apollo-client';
import {durationSec, formatDuration, startOfDay} from './HillpointeRoot';
import styles from './css/HillpointeRoot.module.css';
import {
  HillpointeJobTimingsQuery,
  HillpointeJobTimingsQueryVariables,
} from './types/JobTimingsRoot.types';
import {
  FIFTEEN_SECONDS,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {RunStatus} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {RunStatusTag} from '../runs/RunStatusTag';

// How far back the page looks for runs of each job.
const TIMINGS_DAYS = 90;
// Runs compared for the trend tile: the newest few against the few before them.
const TREND_WINDOW = 5;
const PLOT_HEIGHT = 200;

type TimedRun = Extract<
  HillpointeJobTimingsQuery['runsOrError'],
  {__typename: 'Runs'}
>['results'][number];

type Point = {run: TimedRun; start: number; seconds: number};

/** Every finished run of one job, oldest first, with its duration. */
const pointsFor = (runs: TimedRun[], job: string): Point[] =>
  runs
    .filter((r) => r.pipelineName === job && r.startTime && r.endTime)
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
  const runs = useMemo(() => {
    const result = queryResult.data?.runsOrError;
    return result?.__typename === 'Runs' ? result.results : [];
  }, [queryResult.data]);

  // Jobs ordered by their most recent run, with an average for the picker.
  const jobs = useMemo(() => {
    const byJob = new Map<string, {latest: number; durations: number[]}>();
    runs.forEach((r) => {
      const entry = byJob.get(r.pipelineName) ?? {latest: 0, durations: []};
      entry.latest = Math.max(entry.latest, r.startTime ?? 0);
      const seconds = durationSec(r.startTime, r.endTime);
      if (seconds !== null && r.endTime) {
        entry.durations.push(seconds);
      }
      byJob.set(r.pipelineName, entry);
    });
    return [...byJob.entries()]
      .map(([name, {latest, durations}]) => ({
        name,
        latest,
        avg: average(durations),
        count: durations.length,
      }))
      .sort((a, b) => b.latest - a.latest);
  }, [runs]);

  const selected = jobName ?? jobs[0]?.name ?? null;
  const points = useMemo(() => (selected ? pointsFor(runs, selected) : []), [runs, selected]);

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
        <QueryRefreshCountdown refreshState={refreshState} />
      </Box>
      <div className={styles.timingsGrid}>
        <div className={styles.card}>
          <div className={styles.cardTitle}>Jobs</div>
          <div className={styles.jobList}>
            {jobs.map((job) => (
              <Link
                key={job.name}
                to={`/hillpointe/timings/${encodeURIComponent(job.name)}`}
                className={clsx(styles.jobItem, job.name === selected && styles.jobItemActive)}
              >
                <span className={styles.jobItemName} title={job.name}>
                  {job.name}
                </span>
                <span className={styles.jobItemMeta}>
                  {job.avg === null ? '—' : formatDuration(job.avg)} avg · {job.count} runs
                </span>
              </Link>
            ))}
            {!jobs.length ? (
              <div className={styles.muted}>No runs in the last {TIMINGS_DAYS} days.</div>
            ) : null}
          </div>
        </div>
        {selected ? <JobTimings job={selected} points={points} /> : null}
      </div>
    </div>
  );
};

const JobTimings = ({job, points}: {job: string; points: Point[]}) => {
  const seconds = points.map((p) => p.seconds);
  const avg = average(seconds);
  const fastest = points.length ? points.reduce((a, b) => (b.seconds < a.seconds ? b : a)) : null;
  const slowest = points.length ? points.reduce((a, b) => (b.seconds > a.seconds ? b : a)) : null;
  const last = points[points.length - 1] ?? null;
  const previous = points[points.length - 2] ?? null;

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
          <div className={styles.tileSub}>{points.length} finished runs</div>
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
          <span className={styles.cardSub}>Duration of every finished run, oldest to newest</span>
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

// eslint-disable-next-line import/no-default-export
export default JobTimingsRoot;
