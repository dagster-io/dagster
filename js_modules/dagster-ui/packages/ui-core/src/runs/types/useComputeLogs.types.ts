// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type ComputeLogsSubscriptionVariables = Types.Exact<{
  runId: Types.Scalars['ID'];
  stepKey: Types.Scalars['String'];
  ioType: Types.ComputeIoType;
  cursor?: Types.InputMaybe<Types.Scalars['String']>;
}>;

export type ComputeLogsSubscription = {
  __typename: 'Subscription';
  computeLogs: {
    __typename: 'ComputeLogFile';
    path: string;
    cursor: number;
    data: string | null;
    downloadUrl: string | null;
  };
};

export type ComputeLogForSubscriptionFragment = {
  __typename: 'ComputeLogFile';
  path: string;
  cursor: number;
  data: string | null;
  downloadUrl: string | null;
};
