import {useCallback, useMemo} from 'react';

import {gql, useLazyQuery, useQuery} from '../apollo-client';
import {usePermissionsForLocation} from './Permissions';
import {PipelineSelector} from '../graphql/types';
import {JobPermissionsQuery, JobPermissionsQueryVariables} from './types/useJobPermissions.types';

interface JobPermissionsResult {
  hasLaunchExecutionPermission: boolean;
  hasLaunchReexecutionPermission: boolean;
  loading: boolean;
}

/**
 * Hook for fetching job-specific permissions. If the pipeline selector does not resolve
 * to a pipeline, falls back to location-level permissions.
 */
export const useJobPermissions = (
  pipelineSelector: PipelineSelector,
  locationName: string,
): JobPermissionsResult => {
  const {permissions: locationPermissions} = usePermissionsForLocation(locationName);

  const {data, loading} = useQuery<JobPermissionsQuery, JobPermissionsQueryVariables>(
    JOB_PERMISSIONS_QUERY,
    {
      variables: {selector: pipelineSelector},
    },
  );

  return useMemo<JobPermissionsResult>(() => {
    if (data?.pipelineOrError.__typename === 'Pipeline') {
      return {
        hasLaunchExecutionPermission: data.pipelineOrError.hasLaunchExecutionPermission,
        hasLaunchReexecutionPermission: data.pipelineOrError.hasLaunchReexecutionPermission,
        loading,
      };
    }

    return {
      hasLaunchExecutionPermission: locationPermissions.canLaunchPipelineExecution,
      hasLaunchReexecutionPermission: locationPermissions.canLaunchPipelineReexecution,
      loading,
    };
  }, [data, loading, locationPermissions]);
};

/**
 * Hook for lazily fetching job-specific permissions. If the pipeline selector does not resolve
 * to a pipeline, falls back to location-level permissions.
 */
export const useLazyJobPermissions = (
  pipelineSelector: PipelineSelector,
  locationName: string,
): [() => void, JobPermissionsResult] => {
  const {permissions: locationPermissions} = usePermissionsForLocation(locationName);

  const [fetchPermissions, {data, loading}] = useLazyQuery<
    JobPermissionsQuery,
    JobPermissionsQueryVariables
  >(JOB_PERMISSIONS_QUERY);

  const fetch = useCallback(() => {
    fetchPermissions({variables: {selector: pipelineSelector}});
  }, [fetchPermissions, pipelineSelector]);

  const result = useMemo<JobPermissionsResult>(() => {
    if (data?.pipelineOrError.__typename === 'Pipeline') {
      return {
        hasLaunchExecutionPermission: data.pipelineOrError.hasLaunchExecutionPermission,
        hasLaunchReexecutionPermission: data.pipelineOrError.hasLaunchReexecutionPermission,
        loading,
      };
    }

    return {
      hasLaunchExecutionPermission: locationPermissions.canLaunchPipelineExecution,
      hasLaunchReexecutionPermission: locationPermissions.canLaunchPipelineReexecution,
      loading,
    };
  }, [data, loading, locationPermissions]);

  return [fetch, result];
};

export const JOB_PERMISSIONS_QUERY = gql`
  query JobPermissionsQuery($selector: PipelineSelector!) {
    pipelineOrError(params: $selector) {
      ... on Pipeline {
        id
        hasLaunchExecutionPermission
        hasLaunchReexecutionPermission
      }
    }
  }
`;
