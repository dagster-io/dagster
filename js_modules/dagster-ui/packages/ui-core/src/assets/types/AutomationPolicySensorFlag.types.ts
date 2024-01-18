// Generated GraphQL types, do not edit manually.
import * as Types from '../../graphql/types';

export type AutomationPolicySensorFlagQueryVariables = Types.Exact<{[key: string]: never}>;

export type AutomationPolicySensorFlagQuery = {
  __typename: 'Query';
  instance: {__typename: 'Instance'; id: string; useAutomationPolicySensors: boolean};
};
