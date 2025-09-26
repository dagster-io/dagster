// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type DataQualityExecutionLogsQueryVariables = Types.Exact<{
  executionId: Types.Scalars['String']['input'];
  checkName: Types.Scalars['String']['input'];
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
}>;

export type DataQualityExecutionLogsQuery = {
  __typename: 'Query';
  dataQualityExecutionLogs: {
    __typename: 'InstigationEventConnection';
    cursor: string;
    hasMore: boolean;
    events: Array<{
      __typename: 'InstigationEvent';
      message: string;
      timestamp: string;
      level: Types.LogLevel;
    }>;
  };
};

export const DataQualityExecutionLogsQueryVersion = '63079e9246c10bf35a970b5495d344ef6c2c422d2589289fe7601ceb4cfd3288';
