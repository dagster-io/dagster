// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type CapturedLogsSubscriptionVariables = Types.Exact<{
  logKey: Array<Types.Scalars['String']['input']> | Types.Scalars['String']['input'];
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
}>;

export type CapturedLogsSubscription = {
  __typename: 'Subscription';
  capturedLogs: {
    __typename: 'CapturedLogs';
    stdout: string | null;
    stderr: string | null;
    cursor: string | null;
  };
};

export type CapturedLogFragment = {
  __typename: 'CapturedLogs';
  stdout: string | null;
  stderr: string | null;
  cursor: string | null;
};

export type CapturedLogsMetadataQueryVariables = Types.Exact<{
  logKey: Array<Types.Scalars['String']['input']> | Types.Scalars['String']['input'];
}>;

export type CapturedLogsMetadataQuery = {
  __typename: 'Query';
  capturedLogsMetadata: {
    __typename: 'CapturedLogsMetadata';
    stdoutDownloadUrl: string | null;
    stdoutLocation: string | null;
    stderrDownloadUrl: string | null;
    stderrLocation: string | null;
  };
};

export type CapturedLogsQueryVariables = Types.Exact<{
  logKey: Array<Types.Scalars['String']['input']> | Types.Scalars['String']['input'];
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
  limit?: Types.InputMaybe<Types.Scalars['Int']['input']>;
}>;

export type CapturedLogsQuery = {
  __typename: 'Query';
  capturedLogs: {
    __typename: 'CapturedLogs';
    stdout: string | null;
    stderr: string | null;
    cursor: string | null;
  };
};
