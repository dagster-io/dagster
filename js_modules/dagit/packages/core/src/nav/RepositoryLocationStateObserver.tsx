import {gql, useApolloClient, useSubscription} from '@apollo/client';
import {ButtonLink, ColorsWIP, Group, IconWIP, Caption} from '@dagster-io/ui';
import * as React from 'react';

import {LocationStateChangeEventType} from '../types/globalTypes';
import {WorkspaceContext} from '../workspace/WorkspaceContext';

import {LocationStateChangeSubscription} from './types/LocationStateChangeSubscription';

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
  const {locationEntries, refetch} = React.useContext(WorkspaceContext);
  const [updatedLocations, setUpdatedLocations] = React.useState<string[]>([]);
  const totalMessages = updatedLocations.length;

  useSubscription<LocationStateChangeSubscription>(LOCATION_STATE_CHANGE_SUBSCRIPTION, {
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
  });

  if (!totalMessages) {
    return null;
  }

  return (
    <Group background={ColorsWIP.Gray200} direction="column" spacing={0}>
      {updatedLocations.length > 0 ? (
        <Group padding={{vertical: 8, horizontal: 12}} direction="row" spacing={8}>
          <IconWIP name="warning" color={ColorsWIP.Gray700} />
          <Caption color={ColorsWIP.Gray800}>
            {updatedLocations.length === 1
              ? `Repository location ${updatedLocations[0]} has been updated,` // Be specific when there's only one repository location updated
              : 'One or more repository locations have been updated,'}{' '}
            and new data is available.{' '}
            <ButtonLink
              color={{
                link: ColorsWIP.Gray800,
                hover: ColorsWIP.Gray900,
                active: ColorsWIP.Gray900,
              }}
              underline="always"
              onClick={() => {
                setUpdatedLocations([]);
                refetch();
                client.resetStore();
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
