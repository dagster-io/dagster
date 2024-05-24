// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AutoMaterializeSensorFlagQueryVariables = Types.Exact<{[key: string]: never}>;

export type AutoMaterializeSensorFlagQuery = {
  __typename: 'Query';
  instance: {__typename: 'Instance'; id: string; useAutoMaterializeSensors: boolean};
};
