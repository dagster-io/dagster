import {useContext, useMemo} from 'react';

import {buildAutomationRepoBuckets} from './buildAutomationRepoBuckets';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';

export const useAutomations = () => {
  const {loadingNonAssets: workspaceLoading, data} = useContext(WorkspaceContext);
  useBlockTraceUntilTrue('useAutomations', !workspaceLoading);

  const repoBuckets = useMemo(() => {
    const entries = Object.values(data).filter(
      (location): location is Extract<typeof location, {__typename: 'WorkspaceLocationEntry'}> =>
        location.__typename === 'WorkspaceLocationEntry',
    );
    return buildAutomationRepoBuckets(entries);
  }, [data]);

  const automations = useMemo(() => {
    return repoBuckets.flatMap((bucket) => [...bucket.schedules, ...bucket.sensors]);
  }, [repoBuckets]);

  return {automations, repoBuckets, loading: workspaceLoading};
};
