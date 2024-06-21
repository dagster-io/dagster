// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetNodeInstigatorsFragment = {
  __typename: 'AssetNode';
  id: string;
  targetingInstigators: Array<
    | {
        __typename: 'Schedule';
        scheduleState: {
          __typename: 'InstigationState';
          id: string;
          selectorId: string;
          status: Types.InstigationStatus;
        };
      }
    | {
        __typename: 'Sensor';
        sensorState: {
          __typename: 'InstigationState';
          id: string;
          selectorId: string;
          status: Types.InstigationStatus;
          typeSpecificData:
            | {__typename: 'ScheduleData'}
            | {__typename: 'SensorData'; lastCursor: string | null}
            | null;
        };
      }
  >;
};
