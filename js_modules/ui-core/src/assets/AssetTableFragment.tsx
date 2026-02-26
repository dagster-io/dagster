import {FRESHNESS_POLICY_FRAGMENT} from './FreshnessPolicyFragment';
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
    isAutoCreatedStub
    hasAssetChecks
    computeKind
    hasMaterializePermission
    hasReportRunlessAssetEventPermission
    assetKey {
      path
    }
    internalFreshnessPolicy {
      ...FreshnessPolicyFragment
    }
    partitionDefinition {
      description
      dimensionTypes {
        type
        dynamicPartitionsDefinitionName
      }
    }
    automationCondition {
      label
      expandedLabel
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
    pools
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

  ${FRESHNESS_POLICY_FRAGMENT}
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
