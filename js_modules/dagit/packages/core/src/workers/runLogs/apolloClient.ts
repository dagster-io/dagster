import {ApolloClient, InMemoryCache} from '@apollo/client';
import {WebSocketLink} from '@apollo/client/link/ws';
import {SubscriptionClient} from 'subscriptions-transport-ws';

let apolloClient: ApolloClient<any> | undefined = undefined;

export function setup(data: any) {
  if (apolloClient) {
    throw new Error('Apollo client already setup');
  }
  const websocketURI = `${data.rootServerURI.replace('http', 'ws')}/graphql`;
  const websocketClient = new SubscriptionClient(websocketURI, {
    reconnect: true,
  });

  apolloClient = new ApolloClient({
    cache: new InMemoryCache(),
    link: new WebSocketLink(websocketClient),
  });
}

export function getApolloClient() {
  if (!apolloClient) {
    throw new Error('Apollo Client not setup');
  }
  return apolloClient;
}

export function stop() {
  if (apolloClient) {
    apolloClient.stop();
    apolloClient = undefined;
  }
}
