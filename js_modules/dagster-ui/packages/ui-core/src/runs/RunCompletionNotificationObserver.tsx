import {memo, useCallback, useEffect, useRef, useState} from 'react';

import {gql, useQuery} from '../apollo-client';
import {showSharedToaster} from '../app/DomUtils';
import {RunStatus} from '../graphql/types';
import {AnchorButton} from '../ui/AnchorButton';
import {doneStatuses} from './RunStatuses';

const NOTIFY_RUN_IDS_KEY = 'dagster:notify-run-ids';
export const NOTIFY_RUN_IDS_CHANGED = 'dagster:notify-run-ids-changed';
const POLL_INTERVAL_MS = 5000;

export function getNotifyRunIds(): string[] {
  try {
    const raw = sessionStorage.getItem(NOTIFY_RUN_IDS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === 'string') : [];
  } catch {
    return [];
  }
}

function setNotifyRunIdsStorage(ids: string[]) {
  sessionStorage.setItem(NOTIFY_RUN_IDS_KEY, JSON.stringify(ids));
  document.dispatchEvent(new CustomEvent(NOTIFY_RUN_IDS_CHANGED));
}

export function observeRunCompletion(runId: string): void {
  const ids = getNotifyRunIds();
  if (ids.includes(runId)) return;
  setNotifyRunIdsStorage([...ids, runId]);
}

export function unobserveRunCompletion(runId: string): void {
  const ids = getNotifyRunIds().filter((id) => id !== runId);
  setNotifyRunIdsStorage(ids);
}

export function isObservingRunCompletion(runId: string): boolean {
  return getNotifyRunIds().includes(runId);
}

const RUN_STATUS_QUERY = gql`
  query RunCompletionNotificationStatusQuery($runId: ID!) {
    pipelineRunOrError(runId: $runId) {
      ... on Run {
        id
        status
        pipelineName
      }
    }
  }
`;

interface RunStatusQueryResult {
  pipelineRunOrError:
    | {__typename: 'Run'; id: string; status: RunStatus; pipelineName: string}
    | {__typename: string};
}

function showCompletionToast(runId: string, status: RunStatus, pipelineName: string) {
  const shortId = runId.slice(0, 8);
  const path = `/runs/${runId}`;

  const toastAction = {
    type: 'custom' as const,
    element: <AnchorButton to={path}>View</AnchorButton>,
  };
  const persistentToast = {timeout: Infinity, action: toastAction};

  if (status === RunStatus.SUCCESS) {
    showSharedToaster({
      intent: 'success',
      message: `Run ${shortId} (${pipelineName}) completed successfully`,
      ...persistentToast,
    });
  } else if (status === RunStatus.FAILURE) {
    showSharedToaster({
      intent: 'danger',
      message: `Run ${shortId} (${pipelineName}) failed`,
      ...persistentToast,
    });
  } else if (status === RunStatus.CANCELED) {
    showSharedToaster({
      intent: 'warning',
      message: `Run ${shortId} (${pipelineName}) was canceled`,
      ...persistentToast,
    });
  }
}

interface SingleRunObserverProps {
  runId: string;
  onComplete: (runId: string) => void;
}

const SingleRunCompletionObserver = memo(({runId, onComplete}: SingleRunObserverProps) => {
  const {data} = useQuery<RunStatusQueryResult>(RUN_STATUS_QUERY, {
    variables: {runId},
    pollInterval: POLL_INTERVAL_MS,
    fetchPolicy: 'network-only',
  });

  const notifiedRef = useRef(false);

  useEffect(() => {
    const result = data?.pipelineRunOrError;
    if (result?.__typename !== 'Run' || notifiedRef.current) return;
    const run = result as {id: string; status: RunStatus; pipelineName: string};
    if (!doneStatuses.has(run.status)) return;

    notifiedRef.current = true;
    showCompletionToast(run.id, run.status, run.pipelineName);
    onComplete(runId);
  }, [data, runId, onComplete]);

  return null;
});

export const RunCompletionNotificationObserver = () => {
  const [runIds, setRunIds] = useState<string[]>(() => {
    return getNotifyRunIds();
  });
  const launchedIdsRef = useRef<Set<string>>(new Set());

  const removeRunId = useCallback((runId: string) => {
    launchedIdsRef.current.delete(runId);
    setNotifyRunIdsStorage(getNotifyRunIds().filter((id) => id !== runId));
    setRunIds((prev) => prev.filter((id) => id !== runId));
  }, []);

  useEffect(() => {
    const handleRunLaunched = (e: Event) => {
      const detail = (e as CustomEvent<{runIds?: string[]}>).detail;
      const ids = detail?.runIds;
      if (!Array.isArray(ids) || ids.length === 0) return;
      ids.forEach((id) => launchedIdsRef.current.add(id));
      setRunIds((prev) => {
        const nextSet = new Set(prev);
        ids.forEach((id) => nextSet.add(id));
        return Array.from(nextSet);
      });
    };

    const handleStorageChange = () => {
      setRunIds((prev) => {
        const stored = getNotifyRunIds();
        const merged = new Set([...prev, ...stored, ...launchedIdsRef.current]);
        return Array.from(merged);
      });
    };

    document.addEventListener('run-launched', handleRunLaunched);
    document.addEventListener(NOTIFY_RUN_IDS_CHANGED, handleStorageChange);
    return () => {
      document.removeEventListener('run-launched', handleRunLaunched);
      document.removeEventListener(NOTIFY_RUN_IDS_CHANGED, handleStorageChange);
    };
  }, []);

  useEffect(() => {
    const stored = getNotifyRunIds();
    setRunIds((prev) => {
      const merged = new Set([...prev, ...stored, ...launchedIdsRef.current]);
      return Array.from(merged);
    });
  }, []);

  return (
    <>
      {runIds.map((runId) => (
        <SingleRunCompletionObserver
          key={runId}
          runId={runId}
          onComplete={removeRunId}
        />
      ))}
    </>
  );
};
