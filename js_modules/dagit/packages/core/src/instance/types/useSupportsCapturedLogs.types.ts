// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstanceSupportsCapturedLogsQueryVariables = Types.Exact<{[key: string]: never}>;

export type InstanceSupportsCapturedLogsQuery = {
  __typename: 'DagitQuery';
  instance: {__typename: 'Instance'; id: string; hasCapturedLogManager: boolean};
};
