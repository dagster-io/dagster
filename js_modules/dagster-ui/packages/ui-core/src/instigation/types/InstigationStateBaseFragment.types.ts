// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type InstigationStateBaseFragment = {
  __typename: 'InstigationState';
  id: string;
  selectorId: string;
  name: string;
  instigationType: Types.InstigationType;
  status: Types.InstigationStatus;
  runningCount: number;
};
