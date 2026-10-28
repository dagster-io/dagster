import {
  Button,
  Checkbox,
  Dialog,
  DialogBody,
  DialogFooter,
  Icon,
  NonIdealState,
  Spinner,
} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import {gql, useQuery} from '../../apollo-client';
import {formatElapsedTimeWithoutMsec} from '../Util';
import styles from './css/Mobile.module.css';
import {
  MobileJobAssetsQuery,
  MobileJobAssetsQueryVariables,
  MobileRecentRunsQuery,
  MobileRecentRunsQueryVariables,
} from './types/MobilePipelines.types';
import {isHiddenAssetGroupJob} from '../../asset-graph/Utils';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {RunStatusTag} from '../../runs/RunStatusTag';
import {TimeElapsed} from '../../runs/TimeElapsed';
import {useLaunchWithTelemetry} from '../../shared/launchpad/useLaunchWithTelemetry';
import {TimeFromNow} from '../../ui/TimeFromNow';
import {useRepositoryOptions} from '../../workspace/WorkspaceContext/util';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../QueryRefresh';

const RECENT_RUN_LIMIT = 300;

type Job = {name: string; repositoryName: string; repositoryLocationName: string};
type Run = Extract<MobileRecentRunsQuery['runsOrError'], {__typename: 'Runs'}>['results'][number];

const jobKey = (j: Job) => `${j.repositoryLocationName}:${j.repositoryName}:${j.name}`;

// eslint-disable-next-line import/no-default-export
export default function MobilePipelines() {
  useDocumentTitle('Pipelines');
  const {options, loading: loadingJobs} = useRepositoryOptions();

  const jobs: Job[] = useMemo(
    () =>
      options.flatMap((o) =>
        o.repository.pipelines
          .filter((p) => p.isJob && !isHiddenAssetGroupJob(p.name))
          .map((p) => ({
            name: p.name,
            repositoryName: o.repository.name,
            repositoryLocationName: o.repositoryLocation.name,
          })),
      ),
    [options],
  );

  const queryResult = useQuery<MobileRecentRunsQuery, MobileRecentRunsQueryVariables>(
    MOBILE_RECENT_RUNS_QUERY,
    {variables: {limit: RECENT_RUN_LIMIT}},
  );
  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  // Runs come back newest first, so the first one seen per job is its latest.
  const latestByJob = useMemo(() => {
    const map = new Map<string, Run>();
    const result = queryResult.data?.runsOrError;
    if (result?.__typename === 'Runs') {
      result.results.forEach((run) => {
        const origin = run.repositoryOrigin;
        const key = origin
          ? `${origin.repositoryLocationName}:${origin.repositoryName}:${run.pipelineName}`
          : run.pipelineName;
        if (!map.has(key)) {
          map.set(key, run);
        }
      });
    }
    return map;
  }, [queryResult.data]);

  if (loadingJobs && !jobs.length) {
    return (
      <div className={styles.center}>
        <Spinner purpose="page" />
      </div>
    );
  }
  if (!jobs.length) {
    return <NonIdealState icon="job" title="No pipelines" description="No jobs are loaded." />;
  }

  return (
    <div className={styles.list}>
      {jobs.map((job) => (
        <PipelineCard
          key={jobKey(job)}
          job={job}
          latest={latestByJob.get(jobKey(job)) ?? latestByJob.get(job.name) ?? null}
          onLaunched={() => queryResult.refetch()}
        />
      ))}
    </div>
  );
}

const PipelineCard = ({
  job,
  latest,
  onLaunched,
}: {
  job: Job;
  latest: Run | null;
  onLaunched: () => void;
}) => {
  const launch = useLaunchWithTelemetry();
  const [launching, setLaunching] = useState(false);
  const [picking, setPicking] = useState(false);

  // No asset selection runs the whole job.
  const onRun = async (assetSelection?: {path: string[]}[]) => {
    setLaunching(true);
    try {
      await launch(
        {
          executionParams: {
            selector: {
              repositoryLocationName: job.repositoryLocationName,
              repositoryName: job.repositoryName,
              jobName: job.name,
              assetSelection,
            },
            runConfigData: {},
            mode: 'default',
          },
        },
        {behavior: 'toast'},
      );
      onLaunched();
    } finally {
      setLaunching(false);
    }
  };

  const duration =
    latest?.startTime && latest.endTime
      ? formatElapsedTimeWithoutMsec((latest.endTime - latest.startTime) * 1000)
      : null;

  return (
    <div className={styles.card}>
      <div className={styles.cardMain}>
        <div className={styles.cardName}>{job.name}</div>
        {latest ? (
          <Link to={`/runs/${latest.id}`} className={styles.cardStatus}>
            <RunStatusTag status={latest.status} />
            {latest.startTime ? (
              <span className={styles.cardMeta}>
                <TimeFromNow unixTimestamp={latest.startTime} />
                {duration ? ` · ${duration}` : ''}
                {!latest.endTime ? (
                  <span className={styles.live}>
                    · <TimeElapsed startUnix={latest.startTime} endUnix={null} />
                  </span>
                ) : null}
              </span>
            ) : null}
          </Link>
        ) : (
          <span className={styles.cardMeta}>Never run</span>
        )}
      </div>
      <div className={styles.actions}>
        <Button
          intent="primary"
          icon={<Icon name="execute" />}
          loading={launching}
          onClick={() => onRun()}
          className={styles.runButton}
        >
          Run
        </Button>
        <Button icon={<Icon name="asset" />} onClick={() => setPicking(true)}>
          Assets
        </Button>
      </div>
      {picking ? (
        <AssetPicker
          job={job}
          launching={launching}
          onClose={() => setPicking(false)}
          onRun={async (selection) => {
            await onRun(selection);
            setPicking(false);
          }}
        />
      ) : null}
    </div>
  );
};

// Pick some of a job's assets and run just those.
const AssetPicker = ({
  job,
  launching,
  onClose,
  onRun,
}: {
  job: Job;
  launching: boolean;
  onClose: () => void;
  onRun: (selection: {path: string[]}[]) => void;
}) => {
  const {data, loading} = useQuery<MobileJobAssetsQuery, MobileJobAssetsQueryVariables>(
    MOBILE_JOB_ASSETS_QUERY,
    {
      variables: {
        params: {
          repositoryLocationName: job.repositoryLocationName,
          repositoryName: job.repositoryName,
          pipelineName: job.name,
        },
      },
    },
  );
  const assets = data?.assetNodes ?? [];
  const [selected, setSelected] = useState<Set<string>>(() => new Set());
  const keyOf = (path: string[]) => path.join('/');

  const toggle = (key: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });

  return (
    <Dialog isOpen onClose={onClose} title={job.name} style={{width: 'min(94vw, 480px)'}}>
      <DialogBody>
        {loading ? (
          <Spinner purpose="section" />
        ) : assets.length ? (
          <div className={styles.assetList}>
            {assets.map((a) => {
              const key = keyOf(a.assetKey.path);
              return (
                <Checkbox
                  key={key}
                  checked={selected.has(key)}
                  onChange={() => toggle(key)}
                  label={<span className={styles.assetLabel}>{key}</span>}
                />
              );
            })}
          </div>
        ) : (
          <span className={styles.cardMeta}>This job has no assets.</span>
        )}
      </DialogBody>
      <DialogFooter topBorder>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          intent="primary"
          icon={<Icon name="execute" />}
          disabled={!selected.size}
          loading={launching}
          onClick={() =>
            onRun(
              assets
                .filter((a) => selected.has(keyOf(a.assetKey.path)))
                .map((a) => ({path: a.assetKey.path})),
            )
          }
        >
          Run {selected.size ? `${selected.size} ${selected.size === 1 ? 'asset' : 'assets'}` : ''}
        </Button>
      </DialogFooter>
    </Dialog>
  );
};

export const MOBILE_JOB_ASSETS_QUERY = gql`
  query MobileJobAssetsQuery($params: PipelineSelector!) {
    assetNodes(pipeline: $params) {
      id
      assetKey {
        path
      }
    }
  }
`;

export const MOBILE_RECENT_RUNS_QUERY = gql`
  query MobileRecentRunsQuery($limit: Int!) {
    runsOrError(limit: $limit) {
      ... on Runs {
        results {
          id
          runId
          status
          pipelineName
          startTime
          endTime
          repositoryOrigin {
            id
            repositoryName
            repositoryLocationName
          }
        }
      }
    }
  }
`;
