import {gql} from '../../apollo-client';

export const FULL_PARTITIONS_QUERY = gql`
  query FullPartitionsQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        partitionKeysByDimension {
          name
          type
          partitionKeys
        }
      }
    }
  }
`;
