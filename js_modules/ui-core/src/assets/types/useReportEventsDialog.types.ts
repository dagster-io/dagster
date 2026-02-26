// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

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

export type ReportEventMutationVariables = Types.Exact<{
  eventParams: Types.ReportRunlessAssetEventsParams;
}>;

export type ReportEventMutation = {
  __typename: 'Mutation';
  reportRunlessAssetEvents:
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
        __typename: 'ReportRunlessAssetEventsSuccess';
        assetKey: {__typename: 'AssetKey'; path: Array<string>};
      }
    | {__typename: 'UnauthorizedError'; message: string};
};

export const ReportEventPartitionDefinitionQueryVersion = 'e306421344493a9986106de14bca90ec554505d6f1965991ba502725edc41c95';

export const ReportEventMutationVersion = '80b4987cdf27ec8fac25eb6b98b996bd4fdeb4cbfff605d647da5d4bb8244cb0';
