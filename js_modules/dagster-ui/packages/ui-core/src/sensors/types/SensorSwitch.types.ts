// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type SensorSwitchFragment = {
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
};
