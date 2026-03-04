// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstanceConfigHasInfoQueryVariables = Types.Exact<{[key: string]: never}>;

export type InstanceConfigHasInfoQuery = {
  __typename: 'Query';
  instance: {__typename: 'Instance'; id: string; hasInfo: boolean};
};

export const InstanceConfigHasInfoVersion = '771982a9ee439781255f82986d55aa6a75ab2929d784f2cd27b40f537baf7f27';
