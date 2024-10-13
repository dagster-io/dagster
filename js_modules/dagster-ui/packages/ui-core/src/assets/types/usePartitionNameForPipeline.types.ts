// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetJobPartitionSetsQueryVariables = Types.Exact<{
  pipelineName: Types.Scalars['String']['input'];
  repositoryName: Types.Scalars['String']['input'];
  repositoryLocationName: Types.Scalars['String']['input'];
}>;

export type AssetJobPartitionSetsQuery = {
  __typename: 'Query';
  partitionSetsOrError:
    | {
        __typename: 'PartitionSets';
        results: Array<{
          __typename: 'PartitionSet';
          id: string;
          name: string;
          mode: string;
          solidSelection: Array<string> | null;
        }>;
      }
    | {__typename: 'PipelineNotFoundError'; message: string}
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      };
};

export const AssetJobPartitionSetsQueryVersion = '43286e824ac1f7d1b30c6744ad472c034d8ed257675a720ac53bcf929e0bc7f7';
