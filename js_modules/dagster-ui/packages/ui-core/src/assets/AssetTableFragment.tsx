import {gql} from '../apollo-client';

export const ASSET_TABLE_DEFINITION_FRAGMENT = gql`
  fragment AssetTableDefinitionFragment on AssetNode {
    id
    changedReasons
    groupName
    opNames
    isMaterializable
    isObservable
    isExecutable
    isPartitioned
    computeKind
    hasMaterializePermission
    hasReportRunlessAssetEventPermission
    assetKey {
      path
    }
    partitionDefinition {
      description
      dimensionTypes {
        type
        dynamicPartitionsDefinitionName
      }
    }
    autoMaterializePolicy {
      policyType
    }
    description
    owners {
      ... on UserAssetOwner {
        email
      }
      ... on TeamAssetOwner {
        team
      }
    }
    tags {
      key
      value
    }
    jobNames
    kinds
    repository {
      id
      name
      location {
        id
        name
      }
    }
  }
`;

export const ASSET_TABLE_FRAGMENT = gql`
  fragment AssetTableFragment on Asset {
    id
    key {
      path
    }
    definition {
      id
      ...AssetTableDefinitionFragment
    }
  }

  ${ASSET_TABLE_DEFINITION_FRAGMENT}
`;
