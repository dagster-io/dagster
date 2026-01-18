// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type ResumeBackfillMutationVariables = Types.Exact<{
  backfillId: Types.Scalars['String']['input'];
}>;

export type ResumeBackfillMutation = {
  __typename: 'Mutation';
  resumePartitionBackfill:
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
    | {__typename: 'ResumeBackfillSuccess'; backfillId: string}
    | {__typename: 'UnauthorizedError'; message: string};
};
