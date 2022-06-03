import {gql, useApolloClient} from '@apollo/client';
import React from 'react';

import {AssetKeyInput} from '../types/globalTypes';

import {isHiddenAssetGroupJob} from './Utils';
import {
  AssetForNavigationQuery,
  AssetForNavigationQueryVariables,
} from './types/AssetForNavigationQuery';

export function useFindJobForAsset() {
  const apollo = useApolloClient();

  return React.useCallback(
    async (key: AssetKeyInput): Promise<{opNames: string[]; jobName: string | null}> => {
      const {data} = await apollo.query<AssetForNavigationQuery, AssetForNavigationQueryVariables>({
        query: ASSET_FOR_NAVIGATION_QUERY,
        variables: {key},
      });
      if (data?.assetOrError.__typename === 'Asset' && data?.assetOrError.definition) {
        const def = data.assetOrError.definition;
        return {
          opNames: def.opNames,
          jobName: def.jobNames.find((jobName) => !isHiddenAssetGroupJob(jobName)) || null,
        };
      }
      return {opNames: [], jobName: null};
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
          opNames
          jobNames
        }
      }
    }
  }
`;
