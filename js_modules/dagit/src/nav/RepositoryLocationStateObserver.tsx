import {ApolloClient, gql} from '@apollo/client';
import {Icon, Colors} from '@blueprintjs/core';
import * as React from 'react';
import {useEffect, useState} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {DirectGraphQLSubscription} from 'src/DirectGraphQLSubscription';
import {LocationStateChangeSubscription} from 'src/nav/types/LocationStateChangeSubscription';
import {LocationStateChangeEventType} from 'src/types/globalTypes';
import {ButtonLink} from 'src/ui/ButtonLink';
import {Group} from 'src/ui/Group';
import {Caption} from 'src/ui/Text';
import {useNetworkedRepositoryLocations} from 'src/workspace/WorkspaceContext';

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

interface StateObserverProps {
  client: ApolloClient<any>;
}

export const RepositoryLocationStateObserver = ({client}: StateObserverProps) => {
  const {locations, refetch} = useNetworkedRepositoryLocations();
  const [updatedLocations, setUpdatedLocations] = useState<string[]>([]);
  const [erroredLocations, setErroredLocations] = useState<string[]>([]);
  const totalMessages = updatedLocations.length + erroredLocations.length;

  const networkedErrorLocations = locations
    .filter((location) => location.__typename === 'RepositoryLocationLoadFailure')
    .map((location) => location.name);

  const filteredErroredLocations = erroredLocations.filter(
    (locationName) => !networkedErrorLocations.includes(locationName),
  );

  useEffect(() => {
    const onHandleMessages = (
      messages: LocationStateChangeSubscription[], //   isFirstResponse: boolean,
    ) => {
      const {
        locationStateChangeEvents: {event},
      } = messages[0];
      const {locationName, eventType, serverId} = event;

      switch (eventType) {
        case LocationStateChangeEventType.LOCATION_ERROR:
          setUpdatedLocations((s) => s.filter((name) => name !== locationName));
          setErroredLocations((s) => [...s, locationName]);
          return;
        case LocationStateChangeEventType.LOCATION_UPDATED:
          const matchingRepositoryLocation = locations.find((n) => n.name == locationName);
          if (
            matchingRepositoryLocation &&
            matchingRepositoryLocation?.__typename === 'RepositoryLocation' &&
            matchingRepositoryLocation.serverId !== serverId
          ) {
            setUpdatedLocations((s) => [...s, locationName]);
          }
          return;
        default:
          refetch();
      }
    };

    const subscriptionToken = new DirectGraphQLSubscription<LocationStateChangeSubscription>(
      LOCATION_STATE_CHANGE_SUBSCRIPTION,
      {},
      onHandleMessages,
      () => {}, // https://github.com/dagster-io/dagster/issues/2151
    );

    return () => {
      subscriptionToken.close();
    };
  }, [locations, refetch]);

  return totalMessages > 0 ? (
    <Group background={Colors.GRAY5} direction="vertical" spacing={0}>
      {updatedLocations.length > 0 ? (
        <Group padding={{vertical: 8, horizontal: 12}} direction="horizontal" spacing={8}>
          <Icon icon="warning-sign" color={Colors.DARK_GRAY3} iconSize={14} />
          <Caption color={Colors.DARK_GRAY3}>
            {updatedLocations.length == 1
              ? `Repository location ${updatedLocations[0]} has been updated,` // Be specific when there's only one repository location updated
              : 'One or more repository locations have been updated,'}{' '}
            and new data is available.{' '}
            <ButtonLink
              color={{link: Colors.DARK_GRAY3, hover: Colors.DARK_GRAY1, active: Colors.DARK_GRAY1}}
              underline="always"
              onClick={() => {
                setUpdatedLocations([]);
                setErroredLocations([]);
                refetch();
                client.resetStore();
              }}
            >
              Update data
            </ButtonLink>
          </Caption>
        </Group>
      ) : null}

      {filteredErroredLocations.length > 0 ? (
        <Group padding={{vertical: 8, horizontal: 12}} direction="horizontal" spacing={8}>
          <Icon icon="warning-sign" color={Colors.DARK_GRAY3} iconSize={14} />
          <Caption color={Colors.DARK_GRAY3}>
            An error occurred in a repository location.{' '}
            <DetailLink to="/workspace/repository-locations">View details</DetailLink>
          </Caption>
        </Group>
      ) : null}
    </Group>
  ) : null;
};

const DetailLink = styled(Link)`
  color: ${Colors.DARK_GRAY3};
  text-decoration: underline;

  && :hover,
  :active,
  :visited {
    color: ${Colors.DARK_GRAY1};
  }
`;
