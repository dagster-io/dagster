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
