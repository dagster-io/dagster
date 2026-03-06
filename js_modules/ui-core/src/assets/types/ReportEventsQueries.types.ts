// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ReportCheckEvaluationMutationVariables = Types.Exact<{
  eventParams: Types.ReportAssetCheckEvaluationParams;
}>;

export type ReportCheckEvaluationMutation = {
  __typename: 'Mutation';
  reportAssetCheckEvaluation:
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
        __typename: 'ReportAssetCheckEvaluationSuccess';
        assetKey: {__typename: 'AssetKey'; path: Array<string>};
      }
    | {__typename: 'UnauthorizedError'; message: string};
};

export type ReportEventPartitionDefinitionQueryVariables = Types.Exact<{
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

export const ReportCheckEvaluationMutationVersion = '5450d1bb52007aa1779de02fbadb23c8b657383da672aec583940b8da2083706';

export const ReportEventPartitionDefinitionQueryVersion = 'e306421344493a9986106de14bca90ec554505d6f1965991ba502725edc41c95';
