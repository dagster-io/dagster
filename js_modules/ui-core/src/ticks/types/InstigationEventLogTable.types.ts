/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type LogLevel = 'CRITICAL' | 'DEBUG' | 'ERROR' | 'INFO' | 'WARNING';

export type InstigationEventLogFragment = {
  __typename: 'InstigationEvent';
  message: string;
  timestamp: string;
  level: Types.LogLevel;
};
