// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type RunTimingFragment = {
  __typename: 'Run';
  id: string;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
  status: Types.RunStatus;
  hasConcurrencyKeySlots: boolean;
};
