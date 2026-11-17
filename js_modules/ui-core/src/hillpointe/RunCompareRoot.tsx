import {Box, Colors, NonIdealState, Spinner} from '@dagster-io/ui-components';
import clsx from 'clsx';
import {useMemo, useState} from 'react';
import {Link, useParams} from 'react-router-dom';

import {gql, useQuery} from '../apollo-client';
import {durationSec, formatDuration} from './HillpointeRoot';
import {Delta, JobList, useTimingsData} from './JobTimingsRoot';
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
            Pick two runs of a job to see how long each asset took in one against the other
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

/** One row of run chips; the picked run is highlighted. */
const RunPicker = ({
  label,
  runs,
  picked,
  onPick,
}: {
  label: string;
  runs: ComparedRun[];
  picked: ComparedRun;
  onPick: (runId: string) => void;
}) => (
  <div className={styles.runPickerRow}>
    <div className={styles.runPickerLabel}>{label}</div>
    <div className={styles.runPicker}>
      {runs.map((run) => (
        <button
          key={run.runId}
          type="button"
          className={clsx(styles.runChip, run === picked && styles.runChipActive)}
          onClick={() => onPick(run.runId)}
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
);

const RunTile = ({label, run}: {label: string; run: ComparedRun}) => (
  <div className={styles.tile}>
    <div className={styles.tileLabel}>{label}</div>
    <div className={styles.tileValue}>
      {formatDuration(durationSec(run.startTime, run.endTime))}
    </div>
    <div className={styles.tileSub}>
      <RunStatusTag status={run.status} /> <Link to={`/runs/${run.runId}`}>{runLabel(run)}</Link>
    </div>
  </div>
);

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

  // Until two are picked, the latest run is compared with the one before it.
  const [runId, setRunId] = useState<string | null>(null);
  const [otherId, setOtherId] = useState<string | null>(null);
  const run = runs.find((r) => r.runId === runId) ?? runs[0] ?? null;
  const other = runs.find((r) => r.runId === otherId) ?? runs.find((r) => r !== run) ?? null;

  const comparison = useMemo(() => {
    if (!run || !other) {
      return null;
    }
    const now = stepSeconds(run);
    const then = stepSeconds(other);
    // Every asset either run touched, longest first by whichever run took longer on it.
    const rows = [...new Set([...now.keys(), ...then.keys()])]
      .map((stepKey) => ({
        stepKey,
        seconds: now.get(stepKey) ?? null,
        otherSeconds: then.get(stepKey) ?? null,
      }))
      .sort(
        (a, b) =>
          Math.max(b.seconds ?? 0, b.otherSeconds ?? 0) -
          Math.max(a.seconds ?? 0, a.otherSeconds ?? 0),
      );
    const notable = (row: (typeof rows)[number], sign: 1 | -1) =>
      row.seconds !== null &&
      row.otherSeconds !== null &&
      sign * (row.seconds - row.otherSeconds) >=
        Math.max(NOTABLE_SECS, row.otherSeconds * NOTABLE_FRACTION);
    return {
      rows,
      slower: rows.filter((row) => notable(row, 1)).length,
      faster: rows.filter((row) => notable(row, -1)).length,
      longest: Math.max(1, ...rows.map((row) => Math.max(row.seconds ?? 0, row.otherSeconds ?? 0))),
    };
  }, [run, other]);

  if (result.loading && !result.data) {
    return (
      <div className={styles.card}>
        <Box flex={{justifyContent: 'center'}} padding={32}>
          <Spinner purpose="section" />
        </Box>
      </div>
    );
  }
  if (!run || !other || !comparison) {
    return (
      <div className={styles.card}>
        <NonIdealState
          icon="timer"
          title="Not enough runs"
          description={`${job} needs at least two finished runs to compare.`}
        />
      </div>
    );
  }

  const {rows, slower, faster, longest} = comparison;
  const total = durationSec(run.startTime, run.endTime);
  const otherTotal = durationSec(other.startTime, other.endTime);

  return (
    <div className={clsx(styles.timingsMain, styles.slide)}>
      <div className={styles.card}>
        <div className={styles.cardTitle}>
          {job}
          <span className={styles.cardSub}>Pick one run on each row</span>
        </div>
        <RunPicker label="Run" runs={runs} picked={run} onPick={setRunId} />
        <RunPicker label="Compared with" runs={runs} picked={other} onPick={setOtherId} />
      </div>

      <div className={styles.tiles}>
        <RunTile label="Run" run={run} />
        <RunTile label="Compared with" run={other} />
        <div className={styles.tile}>
          <div className={styles.tileLabel}>Difference</div>
          <div className={styles.tileValue}>
            {total !== null && otherTotal ? <Delta from={otherTotal} to={total} big /> : '—'}
          </div>
          <div className={styles.tileSub}>
            {total !== null && otherTotal !== null
              ? `${formatDuration(Math.abs(total - otherTotal))} ${total >= otherTotal ? 'longer' : 'shorter'} overall`
              : ''}
          </div>
        </div>
        <div className={styles.tile}>
          <div className={styles.tileLabel}>Assets slower</div>
          <div className={clsx(styles.tileValue, slower > 0 && styles.deltaSlower)}>{slower}</div>
          <div className={styles.tileSub}>of {rows.length}</div>
        </div>
        <div className={styles.tile}>
          <div className={styles.tileLabel}>Assets faster</div>
          <div className={clsx(styles.tileValue, faster > 0 && styles.deltaFaster)}>{faster}</div>
          <div className={styles.tileSub}>of {rows.length}</div>
        </div>
      </div>

      <div className={styles.card}>
        <div className={styles.cardTitle}>
          Assets
          <span className={styles.cardSub}>
            Longest first. The top bar is the run; the bar under it is the run it is compared with.
          </span>
        </div>
        <div className={styles.tableWrap}>
          <table className={styles.timingsTable}>
            <thead>
              <tr>
                <th>Asset</th>
                <th className={styles.compareBarCol} />
                <th className={styles.boardNum}>{runLabel(run)}</th>
                <th className={styles.boardNum}>{runLabel(other)}</th>
                <th className={styles.boardNum}>Difference</th>
                <th className={styles.boardNum}>Change</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const both = row.seconds !== null && row.otherSeconds !== null;
                const diff = both ? (row.seconds as number) - (row.otherSeconds as number) : 0;
                return (
                  <tr key={row.stepKey}>
                    <td className={styles.compareName} title={row.stepKey}>
                      {row.stepKey}
                    </td>
                    <td>
                      <div className={styles.compareBars}>
                        <div
                          className={styles.compareBar}
                          style={{
                            width: `${((row.seconds ?? 0) / longest) * 100}%`,
                            background: Colors.dataVizBlue(),
                          }}
                        />
                        <div
                          className={clsx(styles.compareBar, styles.compareBarBaseline)}
                          style={{width: `${((row.otherSeconds ?? 0) / longest) * 100}%`}}
                        />
                      </div>
                    </td>
                    <td className={styles.boardNum}>{formatDuration(row.seconds)}</td>
                    <td className={styles.boardNum}>{formatDuration(row.otherSeconds)}</td>
                    <td className={styles.boardNum}>
                      {both ? `${diff >= 0 ? '+' : '−'}${formatDuration(Math.abs(diff))}` : '—'}
                    </td>
                    <td className={styles.boardNum}>
                      {both && row.otherSeconds ? (
                        <Delta from={row.otherSeconds} to={row.seconds as number} />
                      ) : (
                        '—'
                      )}
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
