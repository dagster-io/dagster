// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type LogTelemetryMutationVariables = Types.Exact<{
  action: Types.Scalars['String'];
  metadata: Types.Scalars['String'];
  clientTime: Types.Scalars['String'];
  clientId: Types.Scalars['String'];
}>;

export type LogTelemetryMutation = {
  __typename: 'Mutation';
  logTelemetry:
    | {__typename: 'LogTelemetrySuccess'; action: string}
    | {
        __typename: 'PythonError';
        message: string;
        stack: Array<string>;
        errorChain: Array<{
          __typename: 'ErrorChainLink';
          isExplicitLink: boolean;
          error: {__typename: 'PythonError'; message: string; stack: Array<string>};
        }>;
      };
};
