import {useQuery} from '@apollo/client';
import {useMemo} from 'react';

import {WORKSPACE_LATEST_STATE_VERSIONS_QUERY} from '../workspace/WorkspaceContext/WorkspaceQueries';

export interface StateVersionInfo {
  name: string;
  version: string | null;
  createTimestamp: number | null;
}

export const useLatestStateVersions = () => {
  const {data, loading, error} = useQuery(WORKSPACE_LATEST_STATE_VERSIONS_QUERY, {
    pollInterval: 5000, // Poll every 5 seconds
    notifyOnNetworkStatusChange: true,
    fetchPolicy: 'cache-and-network',
  });

  const latestStateVersions = useMemo(() => {
    if (data?.workspaceOrError?.__typename !== 'Workspace') {
      return [];
    }
    
    if (!data.workspaceOrError.latestStateVersions?.versionInfo) {
      return [];
    }
    return data.workspaceOrError.latestStateVersions.versionInfo;
  }, [data]);

  return {
    latestStateVersions,
    loading,
    error,
  };
};