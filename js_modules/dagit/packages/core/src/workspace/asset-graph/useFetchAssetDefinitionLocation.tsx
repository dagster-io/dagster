import {gql, useApolloClient} from '@apollo/client';
import React from 'react';

import {AssetKeyInput} from '../../types/globalTypes';

import {
  AssetForNavigationQuery,
  AssetForNavigationQueryVariables,
} from './types/AssetForNavigationQuery';

export function useFetchAssetDefinitionLocation() {
  const apollo = useApolloClient();

  return React.useCallback(
    async (
      key: AssetKeyInput,
    ): Promise<{
      opName: string | null;
      jobName: string | null;
    }> => {
      const {data} = await apollo.query<AssetForNavigationQuery, AssetForNavigationQueryVariables>({
        query: ASSET_FOR_NAVIGATION_QUERY,
        variables: {key},
      });
      if (data?.assetOrError.__typename === 'Asset' && data?.assetOrError.definition) {
        return data?.assetOrError.definition;
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
          jobName
        }
      }
    }
  }
`;
