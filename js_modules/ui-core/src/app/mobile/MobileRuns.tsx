import {ButtonGroup, NonIdealState, Spinner} from '@dagster-io/ui-components';
import {useMemo, useState} from 'react';
import {Link} from 'react-router-dom';

import {useQuery} from '../../apollo-client';
import {formatElapsedTimeWithoutMsec} from '../Util';
import {MOBILE_RECENT_RUNS_QUERY} from './MobilePipelines';
import styles from './css/Mobile.module.css';
import {MobileRecentRunsQuery, MobileRecentRunsQueryVariables} from './types/MobilePipelines.types';
import {RunStatus} from '../../graphql/types';
import {useDocumentTitle} from '../../hooks/useDocumentTitle';
import {RetriedTag, useRetriedSteps} from '../../runs/RunRetriedTag';
import {RunStatusTag} from '../../runs/RunStatusTag';
import {failedStatuses, inProgressStatuses, queuedStatuses} from '../../runs/RunStatuses';
import {TimeElapsed} from '../../runs/TimeElapsed';
import {TimeFromNow} from '../../ui/TimeFromNow';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../QueryRefresh';

const RECENT_RUN_LIMIT = 300;

type Filter = 'all' | 'active' | 'failed' | 'success';

const FILTERS: {id: Filter; label: string}[] = [
  {id: 'all', label: 'All'},
  {id: 'active', label: 'Active'},
  {id: 'failed', label: 'Failed'},
  {id: 'success', label: 'Success'},
];

const matches = (filter: Filter, status: RunStatus) => {
  switch (filter) {
    case 'active':
      return inProgressStatuses.has(status) || queuedStatuses.has(status);
    case 'failed':
      return failedStatuses.has(status);
    case 'success':
      return status === RunStatus.SUCCESS;
    default:
      return true;
  }
};

// eslint-disable-next-line import/no-default-export
export default function MobileRuns() {
  useDocumentTitle('Runs');
  const [filter, setFilter] = useState<Filter>('all');

  const queryResult = useQuery<MobileRecentRunsQuery, MobileRecentRunsQueryVariables>(
    MOBILE_RECENT_RUNS_QUERY,
    {variables: {limit: RECENT_RUN_LIMIT}},
  );
  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const runs = useMemo(() => {
    const result = queryResult.data?.runsOrError;
    const all = result?.__typename === 'Runs' ? result.results : [];
    return all.filter((run) => matches(filter, run.status));
  }, [queryResult.data, filter]);
  const retriedSteps = useRetriedSteps(useMemo(() => runs.map((r) => r.id), [runs]));

  return (
    <>
      <div className={styles.filters}>
        <ButtonGroup<Filter>
          activeItems={new Set([filter])}
          buttons={FILTERS}
          onClick={setFilter}
        />
      </div>
      {!queryResult.data && queryResult.loading ? (
        <div className={styles.center}>
          <Spinner purpose="page" />
        </div>
      ) : runs.length ? (
        <div className={styles.list}>
          {runs.map((run) => {
            const duration =
              run.startTime && run.endTime
                ? formatElapsedTimeWithoutMsec((run.endTime - run.startTime) * 1000)
                : null;
            return (
              <Link key={run.id} to={`/runs/${run.id}`} className={styles.cardLink}>
                <div className={styles.cardMain}>
                  <div className={styles.cardName}>{run.pipelineName}</div>
                  <div className={styles.cardStatus}>
                    <RunStatusTag status={run.status} />
                    <RetriedTag steps={retriedSteps.get(run.id)} short />
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
                </div>
                <span className={styles.cardMeta}>{run.runId.slice(0, 8)}</span>
              </Link>
            );
          })}
        </div>
      ) : (
        <NonIdealState icon="run" title="No runs" description="No recent runs match." />
      )}
    </>
  );
}
