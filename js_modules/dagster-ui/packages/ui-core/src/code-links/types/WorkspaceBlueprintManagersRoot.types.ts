// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type BlueprintManagerFragment = {__typename: 'BlueprintManager'; id: string; name: string};

export type WorkspaceBlueprintManagersQueryVariables = Types.Exact<{
  selector: Types.RepositorySelector;
}>;

export type WorkspaceBlueprintManagersQuery = {
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
        blueprintManagers: {
          __typename: 'BlueprintManagersList';
          results: Array<{__typename: 'BlueprintManager'; id: string; name: string}>;
        };
      }
    | {__typename: 'RepositoryNotFoundError'};
};
