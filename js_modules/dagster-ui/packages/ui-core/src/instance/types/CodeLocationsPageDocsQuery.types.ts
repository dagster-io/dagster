// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type CodeLocationPageDocsQueryVariables = Types.Exact<{[key: string]: never}>;

export type CodeLocationPageDocsQuery = {
  __typename: 'Query';
  repositoriesOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'RepositoryConnection';
        nodes: Array<{
          __typename: 'Repository';
          id: string;
          name: string;
          hasLocationDocs: boolean;
          location: {__typename: 'RepositoryLocation'; name: string; id: string};
        }>;
      }
    | {__typename: 'RepositoryNotFoundError'};
};

export const CodeLocationPageDocsQueryVersion = 'eccd88fc02547dbddcf0257783e1b1bceab26038f754007cfde7c21977a325fb';
