// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ResourceEntryFragment = {
  __typename: 'ResourceDetails';
  name: string;
  description: string | null;
  resourceType: string;
  schedulesUsing: Array<string>;
  sensorsUsing: Array<string>;
  parentResources: Array<{__typename: 'NestedResourceEntry'; name: string}>;
  assetKeysUsing: Array<{__typename: 'AssetKey'; path: Array<string>}>;
  jobsOpsUsing: Array<{__typename: 'JobWithOps'; jobName: string}>;
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
          id: string;
          name: string;
          description: string | null;
          resourceType: string;
          schedulesUsing: Array<string>;
          sensorsUsing: Array<string>;
          parentResources: Array<{__typename: 'NestedResourceEntry'; name: string}>;
          assetKeysUsing: Array<{__typename: 'AssetKey'; path: Array<string>}>;
          jobsOpsUsing: Array<{__typename: 'JobWithOps'; jobName: string}>;
        }>;
      }
    | {__typename: 'RepositoryNotFoundError'};
};

export const WorkspaceResourcesQueryVersion = 'c5f1870a354eb3cf1a94291c56f4477d3462fcece7145bd372b07ef1563f7bd6';
