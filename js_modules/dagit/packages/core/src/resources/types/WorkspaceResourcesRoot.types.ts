// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ResourceEntryFragment = {
  __typename: 'ResourceDetails';
  name: string;
  description: string | null;
  resourceType: string;
  parentResources: Array<{__typename: 'NestedResourceEntry'; name: string}>;
  assetKeysUsing: Array<{__typename: 'AssetKey'; path: Array<string>}>;
  jobsOpsUsing: Array<{__typename: 'JobWithOps'; job: {__typename: 'Job'; id: string}}>;
};

export type WorkspaceResourcesQueryVariables = Types.Exact<{
  selector: Types.RepositorySelector;
}>;

export type WorkspaceResourcesQuery = {
  __typename: 'Query';
  repositoryOrError:
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
        __typename: 'Repository';
        id: string;
        name: string;
        allTopLevelResourceDetails: Array<{
          __typename: 'ResourceDetails';
          name: string;
          description: string | null;
          resourceType: string;
          parentResources: Array<{__typename: 'NestedResourceEntry'; name: string}>;
          assetKeysUsing: Array<{__typename: 'AssetKey'; path: Array<string>}>;
          jobsOpsUsing: Array<{__typename: 'JobWithOps'; job: {__typename: 'Job'; id: string}}>;
        }>;
      }
    | {__typename: 'RepositoryNotFoundError'};
};
