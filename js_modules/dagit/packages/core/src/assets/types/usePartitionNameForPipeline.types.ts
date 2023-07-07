// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetJobPartitionSetsQueryVariables = Types.Exact<{
  pipelineName: Types.Scalars['String'];
  repositoryName: Types.Scalars['String'];
  repositoryLocationName: Types.Scalars['String'];
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
