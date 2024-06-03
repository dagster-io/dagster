import {gql} from '@apollo/client';
import {useContext, useMemo} from 'react';

import {
  LocationFeatureFlagsQuery,
  LocationFeatureFlagsQueryVariables,
} from './types/WorkspaceLocationFeatureFlags.types';
import {AppContext} from '../app/AppContext';
import {showCustomAlert} from '../app/CustomAlertProvider';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {useIndexedDBCachedQuery} from '../search/useIndexedDBCachedQuery';

export const useFeatureFlagForCodeLocation = (locationName: string, flagName: string) => {
  const {localCacheIdPrefix} = useContext(AppContext);
  const {data, fetch: refetch} = useIndexedDBCachedQuery<
    LocationFeatureFlagsQuery,
    LocationFeatureFlagsQueryVariables
  >({
    query: LOCATION_FEATURE_FLAGS_QUERY,
    key: `${localCacheIdPrefix}/${locationName}/LocationFeatureFlags`,
    version: 1,
    variables: useMemo(
      () => ({
        name: locationName,
      }),
      [locationName],
    ),
  });
  useMemo(() => refetch(), [refetch]);

  return useMemo(() => {
    const workspaceLocationEntryOrError = data?.workspaceLocationEntryOrError;
    if (workspaceLocationEntryOrError?.__typename === 'WorkspaceLocationEntry') {
      const matchingFlag = workspaceLocationEntryOrError.featureFlags.find(
        ({name}) => name === flagName,
      );
      if (matchingFlag) {
        return matchingFlag.enabled;
      }
    } else if (workspaceLocationEntryOrError) {
      showCustomAlert({
        title: 'An error occurred',
        body: <PythonErrorInfo error={workspaceLocationEntryOrError} />,
      });
    }
    return false;
  }, [data?.workspaceLocationEntryOrError, flagName]);
};

export const LOCATION_FEATURE_FLAGS_QUERY = gql`
  query LocationFeatureFlagsQuery($name: String!) {
    workspaceLocationEntryOrError(name: $name) {
      ... on WorkspaceLocationEntry {
        id
        featureFlags {
          name
          enabled
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
