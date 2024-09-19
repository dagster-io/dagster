// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type LocationStateChangeSubscriptionVariables = Types.Exact<{[key: string]: never}>;

export type LocationStateChangeSubscription = {
  __typename: 'Subscription';
  locationStateChangeEvents: {
    __typename: 'LocationStateChangeSubscription';
    event: {
      __typename: 'LocationStateChangeEvent';
      message: string;
      locationName: string;
      eventType: Types.LocationStateChangeEventType;
      serverId: string | null;
    };
  };
};

export const LocationStateChangeSubscriptionVersion = 'd6cb6b73be1c484a2f592e60be15fb89b344e385f703ce2c92516e2779df8217';
