import {ButtonLink, Caption, Colors, Group, Icon} from '@dagster-io/ui-components';
import {useContext, useState} from 'react';

import {
  LocationStateChangeSubscription,
  LocationStateChangeSubscriptionVariables,
} from './types/RepositoryLocationStateObserver.types';
import {gql, useApolloClient, useSubscription} from '../apollo-client';
import {LocationStateChangeEventType} from '../graphql/types';
import {WorkspaceContext} from '../workspace/WorkspaceContext/WorkspaceContext';

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
  const {locationEntries, refetch} = useContext(WorkspaceContext);
  const [updatedLocations, setUpdatedLocations] = useState<string[]>([]);
  const totalMessages = updatedLocations.length;

  useSubscription<LocationStateChangeSubscription, LocationStateChangeSubscriptionVariables>(
    LOCATION_STATE_CHANGE_SUBSCRIPTION,
    {
      fetchPolicy: 'no-cache',
      onSubscriptionData: ({subscriptionData}) => {
        const changeEvents = subscriptionData.data?.locationStateChangeEvents;
        if (!changeEvents) {
          return;
        }

        const {locationName, eventType, serverId} = changeEvents.event;

        switch (eventType) {
          case LocationStateChangeEventType.LOCATION_ERROR:
            refetch();
            setUpdatedLocations((s) => s.filter((name) => name !== locationName));
            return;
          case LocationStateChangeEventType.LOCATION_UPDATED:
            const matchingRepositoryLocation = locationEntries.find((n) => n.name === locationName);
            if (
              matchingRepositoryLocation &&
              matchingRepositoryLocation.locationOrLoadError?.__typename === 'RepositoryLocation' &&
              matchingRepositoryLocation.locationOrLoadError?.serverId !== serverId
            ) {
              setUpdatedLocations((s) => [...s, locationName]);
            }
            return;
        }
      },
    },
  );

  if (!totalMessages) {
    return null;
  }

  return (
    <Group background={Colors.backgroundLight()} direction="column" spacing={0}>
      {updatedLocations.length > 0 ? (
        <Group padding={{vertical: 8, horizontal: 12}} direction="row" spacing={8}>
          <Icon name="warning" color={Colors.accentGray()} />
          <Caption color={Colors.textLight()}>
            {updatedLocations.length === 1
              ? `Code location ${updatedLocations[0]} has been updated,` // Be specific when there's only one code location updated
              : 'One or more code locations have been updated,'}
            {' and new data is available. '}
            <ButtonLink
              color={{
                link: Colors.textLight(),
                hover: Colors.textLighter(),
                active: Colors.textLighter(),
              }}
              underline="always"
              onClick={() => {
                setUpdatedLocations([]);
                client.refetchQueries({include: 'active'});
              }}
            >
              Update data
            </ButtonLink>
          </Caption>
        </Group>
      ) : null}
    </Group>
  );
};
