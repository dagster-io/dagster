// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SelectedTickQueryVariables = Types.Exact<{
  instigationSelector: Types.InstigationSelector;
  timestamp: Types.Scalars['Float'];
}>;

export type SelectedTickQuery = {
  __typename: 'Query';
  instigationStateOrError:
    | {
        __typename: 'InstigationState';
        id: string;
        tick: {
          __typename: 'InstigationTick';
          id: string;
          status: Types.InstigationTickStatus;
          timestamp: number;
          skipReason: string | null;
          runIds: Array<string>;
          originRunIds: Array<string>;
          runKeys: Array<string>;
          error: {
            __typename: 'PythonError';
            message: string;
            stack: Array<string>;
            errorChain: Array<{
              __typename: 'ErrorChainLink';
              isExplicitLink: boolean;
              error: {__typename: 'PythonError'; message: string; stack: Array<string>};
            }>;
          } | null;
        } | null;
      }
    | {__typename: 'InstigationStateNotFoundError'}
    | {__typename: 'PythonError'};
};
