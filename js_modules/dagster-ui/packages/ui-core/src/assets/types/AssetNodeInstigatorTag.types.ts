// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetNodeInstigatorsFragment = {
  __typename: 'AssetNode';
  id: string;
  targetingInstigators: Array<
    | {
        __typename: 'Schedule';
        id: string;
        name: string;
        cronSchedule: string;
        executionTimezone: string | null;
        scheduleState: {
          __typename: 'InstigationState';
          id: string;
          selectorId: string;
          status: Types.InstigationStatus;
        };
      }
    | {
        __typename: 'Sensor';
        id: string;
        jobOriginId: string;
        name: string;
        sensorState: {
          __typename: 'InstigationState';
          id: string;
          selectorId: string;
          status: Types.InstigationStatus;
        };
      }
  >;
};
