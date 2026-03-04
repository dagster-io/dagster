// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ResourceEntryFragment = {
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

export const WorkspaceResourcesQueryVersion = 'fe04102e3d1c1951f1424fcb20e83c6ee21705ff170c716480a261d3cb7f73b1';
