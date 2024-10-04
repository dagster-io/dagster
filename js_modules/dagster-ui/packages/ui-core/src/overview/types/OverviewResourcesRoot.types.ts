// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type OverviewResourcesQueryVariables = Types.Exact<{[key: string]: never}>;

export type OverviewResourcesQuery = {
  __typename: 'Query';
  workspaceOrError:
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
        __typename: 'Workspace';
        id: string;
        locationEntries: Array<{
          __typename: 'WorkspaceLocationEntry';
          id: string;
          locationOrLoadError:
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
                __typename: 'RepositoryLocation';
                id: string;
                name: string;
                repositories: Array<{
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
                }>;
              }
            | null;
        }>;
      };
};

export const OverviewResourcesQueryVersion = '38594d66ef4f0161f6cd670cb369ce161f1f4a2b012080af70fb446f600b8cf0';
