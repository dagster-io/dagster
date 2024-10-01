// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type CancelBackfillMutationVariables = Types.Exact<{
  backfillId: Types.Scalars['String']['input'];
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

export const CancelBackfillVersion = '138f5ba5d38b0d939a6a0bf34769cf36c16bb99225204e28e5ab5fcd8baf3194';
