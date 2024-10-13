// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AutoMaterializeSensorFlagQueryVariables = Types.Exact<{[key: string]: never}>;

export type AutoMaterializeSensorFlagQuery = {
  __typename: 'Query';
  instance: {__typename: 'Instance'; id: string; useAutoMaterializeSensors: boolean};
};

export const AutoMaterializeSensorFlagVersion = '961162c030e7e3c35be91db37c1990ad31b53cb8225d216fece2bdc2a6210bce';
