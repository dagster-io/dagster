// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type LaunchAssetWarningsQueryVariables = Types.Exact<{
  upstreamAssetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type LaunchAssetWarningsQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    isMaterializable: boolean;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    partitionDefinition: {
      __typename: 'PartitionDefinition';
      description: string;
      dimensionTypes: Array<{
        __typename: 'DimensionDefinitionType';
        name: string;
        dynamicPartitionsDefinitionName: string | null;
      }>;
    } | null;
  }>;
  instance: {
    __typename: 'Instance';
    id: string;
    runQueuingSupported: boolean;
    daemonHealth: {
      __typename: 'DaemonHealth';
      id: string;
      daemonStatus: {__typename: 'DaemonStatus'; id: string; healthy: boolean | null};
    };
    runLauncher: {__typename: 'RunLauncher'; name: string} | null;
  };
};

export const LaunchAssetWarningsQueryVersion = '1924efd011a8fa46372d16674bca736ef10e46d3aff77430b0bd24461359813e';
