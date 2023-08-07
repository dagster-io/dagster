// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type CancelBackfillMutationVariables = Types.Exact<{
  backfillId: Types.Scalars['String'];
}>;

export type CancelBackfillMutation = {
  __typename: 'Mutation';
  cancelPartitionBackfill:
    | {__typename: 'CancelBackfillSuccess'; backfillId: string}
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
    | {__typename: 'UnauthorizedError'};
};
