// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DisplayedPartitionLabelsQueryVariables = Types.Exact<{
  assetKey: Types.AssetKeyInput;
}>;


export type DisplayedPartitionLabelsQuery = { __typename: 'Query', assetNodeOrError: { __typename: 'AssetNode', id: string, partitionKeyLabels: Array<{ __typename: 'PartitionKeyLabel', key: string, label: string }> } | { __typename: 'AssetNotFoundError' } };

export type LaunchAssetWarningsQueryVariables = Types.Exact<{
  upstreamAssetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;


export type LaunchAssetWarningsQuery = { __typename: 'Query', assetNodes: Array<{ __typename: 'AssetNode', id: string, isMaterializable: boolean, assetKey: { __typename: 'AssetKey', path: Array<string> }, partitionDefinition: { __typename: 'PartitionDefinition', description: string, dimensionTypes: Array<{ __typename: 'DimensionDefinitionType', name: string, dynamicPartitionsDefinitionName: string | null }> } | null }>, instance: { __typename: 'Instance', id: string, runQueuingSupported: boolean, daemonHealth: { __typename: 'DaemonHealth', id: string, daemonStatus: { __typename: 'DaemonStatus', id: string, healthy: boolean | null } }, runLauncher: { __typename: 'RunLauncher', name: string } | null } };

export const DisplayedPartitionLabelsQueryVersion = '0f6be528236c2c0092149cd26185968f7d0ffdb5a94ed8a9ddf1c4695dfbfdaf';

export const LaunchAssetWarningsQueryVersion = '1924efd011a8fa46372d16674bca736ef10e46d3aff77430b0bd24461359813e';
