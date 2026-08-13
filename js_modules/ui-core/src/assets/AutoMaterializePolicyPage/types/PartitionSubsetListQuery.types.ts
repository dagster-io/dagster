/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type AssetJobKeyInput = {
  jobName: string;
};

export type AssetKeyInput = {
  path: Array<string>;
};

export type PartitionSubsetListQueryVariables = Exact<{
  assetKey?: Types.AssetKeyInput | null | undefined;
  assetJobKey?: Types.AssetJobKeyInput | null | undefined;
  evaluationId: string;
  nodeUniqueId: string;
}>;

export type PartitionSubsetListQuery = {
  __typename: 'Query';
  truePartitionsForAutomationConditionEvaluationNode: Array<string>;
};

export const PartitionSubsetListQueryVersion = 'acb33adfd087cf2bc4254fc30332ca01b34c64c116c0c470aa060b39bdbf6323';
