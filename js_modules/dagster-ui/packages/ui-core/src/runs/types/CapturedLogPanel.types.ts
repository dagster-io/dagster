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

export const CapturedLogsSubscriptionVersion = 'fa5e55b59e9d8632ae71a8387c54230ba71e6f57849a974225ba039808acfa93';

export const CapturedLogsMetadataQueryVersion = 'b59ada7585593473002a7b044f09daa85f160445cbc9a4e8ffe0b46d51875cb1';

export const CapturedLogsQueryVersion = '872b617b4f33ee5f6feeba9a4c76ec986fca357695a114e3d7b63172e4600b57';
