// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type CodeLocationHasDocsQueryVariables = Types.Exact<{
  repositorySelector: Types.RepositorySelector;
}>;

export type CodeLocationHasDocsQuery = {
  __typename: 'Query';
  repositoryOrError:
    | {__typename: 'PythonError'}
    | {__typename: 'Repository'; id: string; hasLocationDocs: boolean}
    | {__typename: 'RepositoryNotFoundError'};
};

export const CodeLocationHasDocsQueryVersion = '59aaf373b92f467a40d6c5e9580152565ff47b061d8400db05af584e099cd148';
