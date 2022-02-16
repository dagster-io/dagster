import {gql, useQuery} from '@apollo/client';
import {isEqual} from 'lodash';
import React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP, IconWIP} from '../../../../ui/src';
import {AssetKey} from '../../assets/types';

import {OmittedAssetCountQuery} from './types/OmittedAssetCountQuery';

export const OmittedAssetsNotice: React.FC<{assetKeys: AssetKey[]}> = ({assetKeys}) => {
  const result = useQuery<OmittedAssetCountQuery>(OMITTED_ASSET_COUNT_QUERY);
  const allAssetKeys =
    (result.data?.assetsOrError.__typename === 'AssetConnection' &&
      result.data.assetsOrError.nodes) ||
    [];
  if (allAssetKeys.length === 0) {
    return <span />;
  }

  const assetKeysJSONs = assetKeys.map((key) => JSON.stringify(key));
  const missing = allAssetKeys.filter((a) => !assetKeysJSONs.includes(JSON.stringify(a.key)))
    .length;

  return (
    <Container>
      <IconWIP name="warning" size={16} color={ColorsWIP.Yellow500} />
      {`${missing} asset${missing > 1 ? 's have' : ' has'} no definition`}
    </Container>
  );
};

const Container = styled.div`
  background: ${ColorsWIP.Yellow50};
  border-radius: 8px;
  color: ${ColorsWIP.Yellow700};
  align-items: center;
  display: flex;
  padding: 4px 8px;
  gap: 4px;
`;

const OMITTED_ASSET_COUNT_QUERY = gql`
  query OmittedAssetCountQuery {
    assetsOrError {
      __typename
      ... on AssetConnection {
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
