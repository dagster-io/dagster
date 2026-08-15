/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetCheckSeverity = 'ERROR' | 'WARN';

export type AssetKeyInput = {
  path: Array<string>;
};

export type PartitionDefinitionType = 'DYNAMIC' | 'MULTIPARTITIONED' | 'STATIC' | 'TIME_WINDOW';

export type ReportAssetCheckEvaluationsParams = {
  assetKey: AssetKeyInput;
  checkName: string;
  description?: string | null | undefined;
  partitionKeys?: Array<string | null | undefined> | null | undefined;
  passed: boolean;
  serializedMetadata?: string | null | undefined;
  severity?: AssetCheckSeverity | null | undefined;
};

export type ReportCheckEvaluationMutationVariables = Exact<{
  eventParams: Types.ReportAssetCheckEvaluationsParams;
}>;

export type ReportCheckEvaluationMutation = {
  __typename: 'Mutation';
  reportAssetCheckEvaluations:
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      }
    | {
        __typename: 'ReportAssetCheckEvaluationsSuccess';
        assetKey: {__typename: 'AssetKey'; path: Array<string>};
      }
    | {__typename: 'UnauthorizedError'; message: string};
};

export type ReportEventPartitionDefinitionQueryVariables = Exact<{
  assetKey: Types.AssetKeyInput;
}>;

export type ReportEventPartitionDefinitionQuery = {
  __typename: 'Query';
  assetNodeOrError:
    | {
        __typename: 'AssetNode';
        id: string;
        partitionDefinition: {
          __typename: 'PartitionDefinition';
          type: Types.PartitionDefinitionType;
          name: string | null;
          dimensionTypes: Array<{
            __typename: 'DimensionDefinitionType';
            type: Types.PartitionDefinitionType;
            name: string;
            dynamicPartitionsDefinitionName: string | null;
          }>;
        } | null;
      }
    | {__typename: 'AssetNotFoundError'};
};

export const ReportCheckEvaluationMutationVersion = '4ec348911aefb1eb970aeee3a4528c63729cae42f33a9afae2b8cb767076464f';

export const ReportEventPartitionDefinitionQueryVersion = 'e306421344493a9986106de14bca90ec554505d6f1965991ba502725edc41c95';
