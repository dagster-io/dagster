// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type LogTelemetryMutationVariables = Types.Exact<{
  action: Types.Scalars['String']['input'];
  metadata: Types.Scalars['String']['input'];
  clientTime: Types.Scalars['String']['input'];
  clientId: Types.Scalars['String']['input'];
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

export const LogTelemetryMutationVersion = 'b7bec91d7a5e9e8fb3ad41bb5b7fa1eb1e067c530a8f4cd52a76fde6475462c3';
