import {useCallback, useMemo} from 'react';

import {gql, useLazyQuery, useQuery} from '../apollo-client';
import {usePermissionsForLocation} from './Permissions';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PipelineSelector} from '../graphql/types';
import {JobPermissionsQuery, JobPermissionsQueryVariables} from './types/useJobPermissions.types';

export const useJobPermissions = (pipelineSelector: PipelineSelector, locationName: string) => {
  const {permissions: locationPermissions, loading: locationLoading} =
    usePermissionsForLocation(locationName);
  const {data, loading} = useQuery<JobPermissionsQuery, JobPermissionsQueryVariables>(
    JOB_PERMISSIONS_QUERY,
    {
      variables: {selector: pipelineSelector},
    },
  );

  const {canLaunchPipelineExecution, canLaunchPipelineReexecution} = locationPermissions;
  const fallbackPermissions = useMemo(() => {
    return {canLaunchPipelineExecution, canLaunchPipelineReexecution};
  }, [canLaunchPipelineExecution, canLaunchPipelineReexecution]);

  return useMemo(() => {
    if (data?.pipelineOrError.__typename === 'Pipeline') {
      return {
        hasLaunchExecutionPermission: data.pipelineOrError.hasLaunchExecutionPermission,
        hasLaunchReexecutionPermission: data.pipelineOrError.hasLaunchReexecutionPermission,
        loading,
      };
    }

    return {
      hasLaunchExecutionPermission: fallbackPermissions.canLaunchPipelineExecution,
      hasLaunchReexecutionPermission: fallbackPermissions.canLaunchPipelineReexecution,
      loading: locationLoading,
    };
  }, [data, loading, locationLoading, fallbackPermissions]);
};

export const useLazyJobPermissions = (pipelineSelector: PipelineSelector, locationName: string) => {
  const {permissions: locationPermissions, loading: locationLoading} =
    usePermissionsForLocation(locationName);

  const [fetchPermissions, {data, loading}] = useLazyQuery<
    JobPermissionsQuery,
    JobPermissionsQueryVariables
  >(JOB_PERMISSIONS_QUERY);

  const fetch = useCallback(() => {
    fetchPermissions({variables: {selector: pipelineSelector}});
  }, [fetchPermissions, pipelineSelector]);

  const {canLaunchPipelineExecution, canLaunchPipelineReexecution} = locationPermissions;
  const fallbackPermissions = useMemo(() => {
    return {canLaunchPipelineExecution, canLaunchPipelineReexecution};
  }, [canLaunchPipelineExecution, canLaunchPipelineReexecution]);

  const result = useMemo(() => {
    if (data?.pipelineOrError.__typename === 'Pipeline') {
      return {
        hasLaunchExecutionPermission: data.pipelineOrError.hasLaunchExecutionPermission,
        hasLaunchReexecutionPermission: data.pipelineOrError.hasLaunchReexecutionPermission,
        loading,
      };
    }

    return {
      hasLaunchExecutionPermission: fallbackPermissions.canLaunchPipelineExecution,
      hasLaunchReexecutionPermission: fallbackPermissions.canLaunchPipelineReexecution,
      loading: locationLoading,
    };
  }, [data, loading, locationLoading, fallbackPermissions]);

  return [fetch, result];
};

export const JOB_PERMISSIONS_QUERY = gql`
  query JobPermissionsQuery($selector: PipelineSelector!) {
    pipelineOrError(params: $selector) {
      ...PythonErrorFragment
      ... on PipelineNotFoundError {
        message
      }
      ... on InvalidSubsetError {
        message
      }
      ... on Pipeline {
        id
        hasLaunchExecutionPermission
        hasLaunchReexecutionPermission
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
