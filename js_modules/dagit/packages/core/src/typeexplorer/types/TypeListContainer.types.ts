// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type TypeListContainerQueryVariables = Types.Exact<{
  pipelineSelector: Types.PipelineSelector;
}>;

export type TypeListContainerQuery = {
  __typename: 'Query';
  pipelineOrError:
    | {__typename: 'InvalidSubsetError'}
    | {
        __typename: 'Pipeline';
        id: string;
        isJob: boolean;
        name: string;
        dagsterTypes: Array<
          | {
              __typename: 'ListDagsterType';
              name: string | null;
              isBuiltin: boolean;
              displayName: string;
              description: string | null;
            }
          | {
              __typename: 'NullableDagsterType';
              name: string | null;
              isBuiltin: boolean;
              displayName: string;
              description: string | null;
            }
          | {
              __typename: 'RegularDagsterType';
              name: string | null;
              isBuiltin: boolean;
              displayName: string;
              description: string | null;
            }
        >;
      }
    | {__typename: 'PipelineNotFoundError'}
    | {__typename: 'PythonError'};
};
