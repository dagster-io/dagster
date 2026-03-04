// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type CodeLocationDocsQueryVariables = Types.Exact<{
  repositorySelector: Types.RepositorySelector;
}>;

export type CodeLocationDocsQuery = {
  __typename: 'Query';
  repositoryOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Repository';
        id: string;
        locationDocsJsonOrError:
          | {__typename: 'LocationDocsJson'; json: any}
          | {__typename: 'PythonError'; message: string};
      }
    | {__typename: 'RepositoryNotFoundError'};
};

export const CodeLocationDocsQueryVersion = 'cde585a103c0857a37a332bedf2fa15660be9b328849497fade5728947a8cbd5';
