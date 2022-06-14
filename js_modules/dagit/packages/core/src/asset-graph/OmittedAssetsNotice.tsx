import {gql, useQuery} from '@apollo/client';
import {Colors} from '@dagster-io/ui';
import React from 'react';
import styled from 'styled-components/macro';

import {AssetKey} from '../assets/types';

import {OmittedAssetCountQuery} from './types/OmittedAssetCountQuery';

export const OmittedAssetsNotice: React.FC<{assetKeys: AssetKey[]}> = ({assetKeys}) => {
  const result = useQuery<OmittedAssetCountQuery>(OMITTED_ASSET_COUNT_QUERY);
  const allMaterializationKeys =
    (result.data?.materializedKeysOrError.__typename === 'MaterializedKeysConnection' &&
      result.data.materializedKeysOrError.nodes) ||
    [];
  if (allMaterializationKeys.length === 0) {
    return <span />;
  }

  const assetKeysJSONs = assetKeys.map((key) => JSON.stringify(key));
  const materializationsNotShown = allMaterializationKeys.filter(
    (a) => !assetKeysJSONs.includes(JSON.stringify(a.key)),
  ).length;

  if (materializationsNotShown === 0) {
    return <span />;
  }
  return <Container>Only software-defined assets are shown</Container>;
};

const Container = styled.div`
  background: ${Colors.Gray100};
  border-radius: 8px;
  color: ${Colors.Gray500};
  align-items: center;
  display: flex;
  padding: 4px 8px;
  gap: 4px;
`;

const OMITTED_ASSET_COUNT_QUERY = gql`
  query OmittedAssetCountQuery {
    materializedKeysOrError {
      __typename
      ... on MaterializedKeysConnection {
        nodes {
          id
          key {
            path
          }
        }
      }
    }
  }
`;
