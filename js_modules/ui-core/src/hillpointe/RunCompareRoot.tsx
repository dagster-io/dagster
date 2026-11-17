import {Box, Colors, NonIdealState, Spinner} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {useMemo, useState} from 'react';
import {Link, useParams} from 'react-router-dom';

import {gql, useQuery} from '../apollo-client';
import {durationSec, formatDuration} from './HillpointeRoot';
import {Delta, JobList, average, useTimingsData} from './JobTimingsRoot';
import styles from './css/HillpointeRoot.module.css';
import {
  HillpointeRunCompareQuery,
  HillpointeRunCompareQueryVariables,
} from './types/RunCompareRoot.types';
import {QueryRefreshCountdown} from '../app/QueryRefresh';
import {useTrackPageView} from '../app/analytics';
import {RunStatus} from '../graphql/types';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {RunStatusTag} from '../runs/RunStatusTag';

// How many of a job's most recent finished runs can be picked for comparison.
const RECENT_RUNS = 12;
// The picked run is compared with the average of up to this many successful runs before it.
const BASELINE_RUNS = 5;
// An asset counts as slower or faster only when it moved by at least this share
// and this many seconds, so a 1s asset taking 2s is not flagged.
const NOTABLE_FRACTION = 0.1;
const NOTABLE_SECS = 2;

type ComparedRun = Extract<
  HillpointeRunCompareQuery['runsOrError'],
  {__typename: 'Runs'}
>['results'][number];

/** Seconds each step of a run took, for the steps that finished. */
const stepSeconds = (run: ComparedRun) => {
  const map = new Map<string, number>();
  run.stepStats.forEach((step) => {
    const seconds = durationSec(step.startTime, step.endTime);
    if (seconds !== null) {
      map.set(step.stepKey, seconds);
    }
  });
  return map;
};

const runLabel = (run: ComparedRun) =>
  new Date((run.startTime ?? 0) * 1000).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });

export const RunCompareRoot = () => {
  useTrackPageView();
  useDocumentTitle('Compare runs');
  const {jobName} = useParams<{jobName?: string}>();
  const {queryResult, refreshState, jobs, locations} = useTimingsData();
  const job = jobName ?? jobs[0]?.name ?? null;

  if (queryResult.loading && !jobs.length) {
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
          Compare runs
          <span className={styles.cardSub}>
            How long each asset took in one run, against the runs before it
          </span>
        </div>
        <QueryRefreshCountdown refreshState={refreshState} />
      </Box>
      <div className={styles.timingsGrid}>
        <JobList jobs={jobs} locations={locations} selected={job} basePath="/hillpointe/compare" />
        {job ? <JobComparison key={job} job={job} /> : null}
      </div>
    </div>
  );
};

const JobComparison = ({job}: {job: string}) => {
  const result = useQuery<HillpointeRunCompareQuery, HillpointeRunCompareQueryVariables>(
    HILLPOINTE_RUN_COMPARE_QUERY,
    {variables: {job, limit: RECENT_RUNS}},
  );
  // Newest first, as the API returns them; unfinished runs have nothing to compare.
  const runs = useMemo(() => {
    const data = result.data?.runsOrError;
    const all = data?.__typename === 'Runs' ? data.results : [];
    return all.filter((r) => r.startTime && r.endTime);
  }, [result.data]);

  const [pickedId, setPickedId] = useState<string | null>(null);
  const index = Math.max(
    0,
    runs.findIndex((r) => r.runId === pickedId),
  );
  const picked = runs[index] ?? null;

  const comparison = useMemo(() => {
    if (!picked) {
      return null;
    }
    // The baseline is successful runs only: a failed run stops early, which
    // would make everything after it look slow by comparison.
    const earlier = runs
      .slice(index + 1)
      .filter((r) => r.status === RunStatus.SUCCESS)
      .slice(0, BASELINE_RUNS);
    const now = stepSeconds(picked);
    const before = earlier.map(stepSeconds);
    const rows = [...now.entries()]
      .map(([stepKey, seconds]) => ({
        stepKey,
        seconds,
        previous: before[0]?.get(stepKey) ?? null,
        avg: average(before.flatMap((m) => (m.has(stepKey) ? [m.get(stepKey) as number] : []))),
      }))
      .sort((a, b) => b.seconds - a.seconds);
    const totals = earlier.map((r) => durationSec(r.startTime, r.endTime) ?? 0);
    const notable = (row: (typeof rows)[number], sign: 1 | -1) =>
      row.avg !== null &&
      sign * (row.seconds - row.avg) >= Math.max(NOTABLE_SECS, row.avg * NOTABLE_FRACTION);
    return {
      earlier,
      rows,
      total: durationSec(picked.startTime, picked.endTime),
      previousTotal: totals[0] ?? null,
      avgTotal: average(totals),
      slower: rows.filter((row) => notable(row, 1)).length,
      faster: rows.filter((row) => notable(row, -1)).length,
      longest: Math.max(1, ...rows.map((row) => Math.max(row.seconds, row.avg ?? 0))),
    };
  }, [runs, index, picked]);

  if (result.loading && !result.data) {
    return (
      <div className={styles.card}>
        <Box flex={{justifyContent: 'center'}} padding={32}>
          <Spinner purpose="section" />
        </Box>
      </div>
    );
  }
  if (!picked || !comparison) {
    return (
      <div className={styles.card}>
        <NonIdealState
          icon="timer"
          title="No finished runs"
          description={`${job} has no finished runs to compare.`}
        />
      </div>
    );
  }

  const {earlier, rows, total, previousTotal, avgTotal, slower, faster, longest} = comparison;
  const baseline = earlier.length;

  return (
    <div className={clsx(styles.timingsMain, styles.slide)}>
      <div className={styles.card}>
        <div className={styles.cardTitle}>
          {job}
          <span className={styles.cardSub}>Pick the run to look at</span>
        </div>
        <div className={styles.runPicker}>
          {runs.map((run, i) => (
            <button
              key={run.runId}
              type="button"
              className={clsx(styles.runChip, i === index && styles.runChipActive)}
              onClick={() => setPickedId(run.runId)}
            >
              <span
                className={styles.runChipDot}
                style={{
                  background:
                    run.status === RunStatus.SUCCESS ? Colors.dataVizGreen() : Colors.dataVizRed(),
                }}
              />
              {runLabel(run)}
            </button>
          ))}
        </div>
      </div>

      <div className={styles.tiles}>
        <div className={styles.tile}>
          <div className={styles.tileLabel}>This run</div>
          <div className={styles.tileValue}>{formatDuration(total)}</div>
          <div className={styles.tileSub}>
            <RunStatusTag status={picked.status} />{' '}
            <Link to={`/runs/${picked.runId}`}>Open run</Link>
          </div>
        </div>
        <div className={styles.tile}>
          <div className={styles.tileLabel}>Previous run</div>
          <div className={styles.tileValue}>{formatDuration(previousTotal)}</div>
          <div className={styles.tileSub}>
            {total !== null && previousTotal ? (
              <Delta from={previousTotal} to={total} />
            ) : (
              'No earlier run'
            )}
          </div>
        </div>
        <div className={styles.tile}>
          <div className={styles.tileLabel}>Average before</div>
          <div className={styles.tileValue}>{formatDuration(avgTotal)}</div>
          <div className={styles.tileSub}>
            {total !== null && avgTotal ? (
              <Delta from={avgTotal} to={total} label={`vs last ${baseline}`} />
            ) : (
              'No earlier run'
            )}
          </div>
        </div>
        <div className={styles.tile}>
          <div className={styles.tileLabel}>Assets slower</div>
          <div className={clsx(styles.tileValue, slower > 0 && styles.deltaSlower)}>{slower}</div>
          <div className={styles.tileSub}>of {rows.length}, against the average</div>
        </div>
        <div className={styles.tile}>
          <div className={styles.tileLabel}>Assets faster</div>
          <div className={clsx(styles.tileValue, faster > 0 && styles.deltaFaster)}>{faster}</div>
          <div className={styles.tileSub}>of {rows.length}, against the average</div>
        </div>
      </div>

      <div className={styles.card}>
        <div className={styles.cardTitle}>
          Assets
          <span className={styles.cardSub}>
            Longest first. Top bar is this run; the bar under it is the average of the{' '}
            {baseline === 1 ? 'successful run' : `${baseline} successful runs`} before it.
          </span>
        </div>
        <div className={styles.tableWrap}>
          <table className={styles.timingsTable}>
            <thead>
              <tr>
                <th>Asset</th>
                <th className={styles.compareBarCol} />
                <th className={styles.boardNum}>This run</th>
                <th className={styles.boardNum}>Previous</th>
                <th className={styles.boardNum}>Average</th>
                <th className={styles.boardNum}>vs previous</th>
                <th className={styles.boardNum}>vs average</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.stepKey}>
                  <td className={styles.compareName} title={row.stepKey}>
                    {row.stepKey}
                  </td>
                  <td>
                    <div className={styles.compareBars}>
                      <div
                        className={styles.compareBar}
                        style={{
                          width: `${(row.seconds / longest) * 100}%`,
                          background: Colors.dataVizBlue(),
                        }}
                      />
                      <div
                        className={clsx(styles.compareBar, styles.compareBarBaseline)}
                        style={{width: `${((row.avg ?? 0) / longest) * 100}%`}}
                      />
                    </div>
                  </td>
                  <td className={styles.boardNum}>{formatDuration(row.seconds)}</td>
                  <td className={styles.boardNum}>{formatDuration(row.previous)}</td>
                  <td className={styles.boardNum}>{formatDuration(row.avg)}</td>
                  <td className={styles.boardNum}>
                    {row.previous ? <Delta from={row.previous} to={row.seconds} /> : '—'}
                  </td>
                  <td className={styles.boardNum}>
                    {row.avg ? <Delta from={row.avg} to={row.seconds} /> : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Step timings come from the event log, so this is asked for one job's recent
// runs only.
export const HILLPOINTE_RUN_COMPARE_QUERY = gql`
  query HillpointeRunCompareQuery($job: String!, $limit: Int!) {
    runsOrError(filter: {pipelineName: $job, statuses: [SUCCESS, FAILURE]}, limit: $limit) {
      ... on Runs {
        results {
          id
          runId
          status
          startTime
          endTime
          stepStats {
            stepKey
            startTime
            endTime
          }
        }
      }
    }
  }
`;

// Imported via React.lazy, which requires a default export.
// eslint-disable-next-line import/no-default-export
export default RunCompareRoot;
