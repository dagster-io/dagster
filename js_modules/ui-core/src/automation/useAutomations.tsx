import {useContext, useMemo} from 'react';

import {buildAutomationRepoBuckets} from './buildAutomationRepoBuckets';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';

export const useAutomations = () => {
  const {
    loadingNonAssets: workspaceLoading,
    data,
    codeLocationFilter,
  } = useContext(WorkspaceContext);
  useBlockTraceUntilTrue('useAutomations', !workspaceLoading);

  const repoBuckets = useMemo(() => {
    const entries = Object.values(data).filter(
      (location): location is Extract<typeof location, {__typename: 'WorkspaceLocationEntry'}> =>
        location.__typename === 'WorkspaceLocationEntry' &&
        (!codeLocationFilter || location.name === codeLocationFilter),
    );
    return buildAutomationRepoBuckets(entries);
  }, [data, codeLocationFilter]);

  const automations = useMemo(() => {
    return repoBuckets.flatMap((bucket) => [...bucket.schedules, ...bucket.sensors]);
  }, [repoBuckets]);

  return {automations, repoBuckets, loading: workspaceLoading};
};
