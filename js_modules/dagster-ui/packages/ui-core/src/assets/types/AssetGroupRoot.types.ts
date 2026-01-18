// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetGroupMetadataQueryVariables = Types.Exact<{
  selector: Types.AssetGroupSelector;
}>;

export type AssetGroupMetadataQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    automationCondition: {__typename: 'AutomationCondition'} | null;
  }>;
};

export const AssetGroupMetadataQueryVersion = '649fd8034ea453acebec574365ec19b678930cdbc976f5da2addfe40f985886f';
