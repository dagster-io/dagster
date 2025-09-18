// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetCheckLogsPageQueryVariables = Types.Exact<{
  runId: Types.Scalars['String']['input'];
  checkKey: Types.Scalars['String']['input'];
  cursor?: Types.InputMaybe<Types.Scalars['String']['input']>;
}>;

export type AssetCheckLogsPageQuery = {
  __typename: 'Query';
  assetChecklogEvents: {
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

export const AssetCheckLogsPageQueryVersion = '63a4be64cfcd1b1afbd9b7e6725193c2218ffc730885e83df6378af0dc92057f';
