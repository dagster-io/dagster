import {gql, useApolloClient, useSubscription} from '../apollo-client';
import {
  LocationStateChangeSubscription,
  LocationStateChangeSubscriptionVariables,
} from './types/RepositoryLocationStateObserver.types';
import {LocationStateChangeEventType} from '../graphql/types';

const LOCATION_STATE_CHANGE_SUBSCRIPTION = gql`
  subscription LocationStateChangeSubscription {
    locationStateChangeEvents {
      event {
        message
        locationName
        eventType
        serverId
      }
    }
  }
`;

export const RepositoryLocationStateObserver = () => {
  const client = useApolloClient();

  useSubscription<LocationStateChangeSubscription, LocationStateChangeSubscriptionVariables>(
    LOCATION_STATE_CHANGE_SUBSCRIPTION,
    {
      fetchPolicy: 'no-cache',
      onSubscriptionData: ({subscriptionData}) => {
        const changeEvents = subscriptionData.data?.locationStateChangeEvents;
        if (!changeEvents) {
          return;
        }

        const {eventType} = changeEvents.event;

        switch (eventType) {
          case LocationStateChangeEventType.LOCATION_ERROR:
          case LocationStateChangeEventType.LOCATION_UPDATED:
            console.log('refetching due to location update or error');
            client.refetchQueries({include: 'active'});
        }
      },
    },
  );

  return null;
};
