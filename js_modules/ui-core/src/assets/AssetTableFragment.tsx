import {FRESHNESS_POLICY_FRAGMENT} from './FreshnessPolicyFragment';
import {gql} from '../apollo-client';

// Asset node fields that don't depend on the surrounding repository / location
// context. Composed by the workspace query (which stamps `repository`
// client-side from the parent context) and by `ASSET_WORKSPACE_NODE_FRAGMENT`
// (which adds `repository` directly via `ASSET_NODE_REPOSITORY_FRAGMENT`).
export const ASSET_BASE_NODE_FRAGMENT = gql`
  fragment AssetBaseNodeFragment on AssetNode {
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
    hasWipePermission
    hasReportRunlessAssetEventPermission
    assetKey {
      path
    }
    internalFreshnessPolicy {
      ...FreshnessPolicyFragment
    }
    partitionDefinition {
      dimensionTypes {
        type
        dynamicPartitionsDefinitionName
      }
    }
    automationCondition {
      __typename
    }
    description(characterLimit: 240)
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
    storageAddress {
      storageKind
      tableName
    }
    jobNames
    kinds
  }

  ${FRESHNESS_POLICY_FRAGMENT}
`;

export const ASSET_NODE_REPOSITORY_FRAGMENT = gql`
  fragment AssetNodeRepositoryFragment on AssetNode {
    id
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

// Self-contained per-asset shape that includes its own `repository`. Used by
// non-workspace queries (asset table, asset catalog group) where the consumer
// doesn't have a surrounding repo/location context to stamp from. The merged
// `WorkspaceAssetNode` TS type in `useAllAssets.tsx` is the workspace-level
// superset of this — same fields plus `dependedByKeys` and `repository`
// (the chosen representative when an asset is defined in multiple repos).
export const ASSET_WORKSPACE_NODE_FRAGMENT = gql`
  fragment AssetWorkspaceNodeFragment on AssetNode {
    id
    ...AssetBaseNodeFragment
    ...AssetNodeRepositoryFragment
  }

  ${ASSET_BASE_NODE_FRAGMENT}
  ${ASSET_NODE_REPOSITORY_FRAGMENT}
`;

export const ASSET_TABLE_FRAGMENT = gql`
  fragment AssetTableFragment on Asset {
    id
    key {
      path
    }
    definition {
      id
      ...AssetWorkspaceNodeFragment
    }
  }

  ${ASSET_WORKSPACE_NODE_FRAGMENT}
`;
