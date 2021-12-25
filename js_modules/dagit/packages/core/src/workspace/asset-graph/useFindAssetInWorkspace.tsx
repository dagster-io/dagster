import {gql, useApolloClient} from '@apollo/client';
import React from 'react';

import {AssetKeyInput} from '../../types/globalTypes';

import {
  AssetForNavigationQuery,
  AssetForNavigationQueryVariables,
} from './types/AssetForNavigationQuery';

export function useFindAssetInWorkspace() {
  const apollo = useApolloClient();

  return React.useCallback(
    async (key: AssetKeyInput): Promise<{opName: string | null; jobName: string | null}> => {
      const {data} = await apollo.query<AssetForNavigationQuery, AssetForNavigationQueryVariables>({
        query: ASSET_FOR_NAVIGATION_QUERY,
        variables: {key},
      });
      if (data?.assetOrError.__typename === 'Asset' && data?.assetOrError.definition) {
        const def = data.assetOrError.definition;
        return {opName: def.opName, jobName: def.jobs[0]?.name || null};
      }
      return {opName: null, jobName: null};
    },
    [apollo],
  );
}

const ASSET_FOR_NAVIGATION_QUERY = gql`
  query AssetForNavigationQuery($key: AssetKeyInput!) {
    assetOrError(assetKey: $key) {
      __typename
      ... on Asset {
        id
        definition {
          id
          opName
          jobs {
            id
            name
          }
        }
      }
    }
  }
`;
