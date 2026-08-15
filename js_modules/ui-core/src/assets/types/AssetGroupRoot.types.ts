/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetGroupSelector = {
  groupName: string;
  repositoryLocationName: string;
  repositoryName: string;
};

export type AssetGroupMetadataQueryVariables = Exact<{
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
