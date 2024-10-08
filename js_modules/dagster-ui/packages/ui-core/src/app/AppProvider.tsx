import {RetryLink} from '@apollo/client/link/retry';
import {WebSocketLink} from '@apollo/client/link/ws';
import {getMainDefinition} from '@apollo/client/utilities';
import {CustomTooltipProvider} from '@dagster-io/ui-components';
import * as React from 'react';
import {useContext} from 'react';
import {BrowserRouter} from 'react-router-dom';
import {CompatRouter} from 'react-router-dom-v5-compat';
import {SubscriptionClient} from 'subscriptions-transport-ws';
import {v4 as uuidv4} from 'uuid';

import {AppContext} from './AppContext';
import {CustomAlertProvider} from './CustomAlertProvider';
import {CustomConfirmationProvider} from './CustomConfirmationProvider';
import {DagsterPlusLaunchPromotion} from './DagsterPlusLaunchPromotion';
import {GlobalStyleProvider} from './GlobalStyleProvider';
import {LayoutProvider} from './LayoutProvider';
import {createOperationQueryStringApolloLink} from './OperationQueryStringApolloLink';
import {PermissionsProvider} from './Permissions';
import {patchCopyToRemoveZeroWidthUnderscores} from './Util';
import {WebSocketProvider} from './WebSocketProvider';
import {AnalyticsContext, dummyAnalytics} from './analytics';
import {migrateLocalStorageKeys} from './migrateLocalStorageKeys';
import {TimeProvider} from './time/TimeContext';
import {
  ApolloClient,
  ApolloLink,
  ApolloProvider,
  HttpLink,
  InMemoryCache,
  split,
} from '../apollo-client';
import {AssetLiveDataProvider} from '../asset-data/AssetLiveDataProvider';
import {AssetRunLogObserver} from '../asset-graph/AssetRunLogObserver';
import {CodeLinkProtocolProvider} from '../code-links/CodeLinkProtocol';
import {DeploymentStatusProvider, DeploymentStatusType} from '../instance/DeploymentStatusProvider';
import {InstancePageContext} from '../instance/InstancePageContext';
import {WorkspaceProvider} from '../workspace/WorkspaceContext/WorkspaceContext';
import './blueprint.css';

// The solid sidebar and other UI elements insert zero-width spaces so solid names
// break on underscores rather than arbitrary characters, but we need to remove these
// when you copy-paste so they don't get pasted into editors, etc.
patchCopyToRemoveZeroWidthUnderscores();

const idempotencyLink = new ApolloLink((operation, forward) => {
  if (/^\s*mutation/.test(operation.query.loc?.source.body ?? '')) {
    operation.setContext(({headers = {}}) => ({
      headers: {
        ...headers,
        'Idempotency-Key': uuidv4(),
      },
    }));
  }
  return forward(operation);
});

const httpStatusCodesToRetry = new Set([502, 503, 504, 429, 409]);

export interface AppProviderProps {
  children: React.ReactNode;
  appCache: InMemoryCache;
  config: {
    apolloLinks: ApolloLink[];
    basePath?: string;
    headers?: {[key: string]: string};
    origin: string;
    telemetryEnabled?: boolean;
    statusPolling: Set<DeploymentStatusType>;
  };

  // Used for localStorage/IndexedDB caching to be isolated between instances/deployments
  localCacheIdPrefix?: string;
}

export const AppProvider = (props: AppProviderProps) => {
  const {appCache, config, localCacheIdPrefix} = props;
  const {
    apolloLinks,
    basePath = '',
    headers = {},
    origin,
    telemetryEnabled = false,
    statusPolling,
  } = config;

  // todo dish: Change `deleteExisting` to true soon. (Current: 1.4.5)
  React.useEffect(() => {
    migrateLocalStorageKeys({from: /DAGIT_FLAGS/g, to: 'DAGSTER_FLAGS', deleteExisting: false});
    migrateLocalStorageKeys({from: /:dagit/gi, to: ':dagster', deleteExisting: false});
    migrateLocalStorageKeys({from: /^dagit(\.v2)?/gi, to: 'dagster', deleteExisting: false});
  }, []);

  const graphqlPath = `${basePath}/graphql`;
  const rootServerURI = `${origin}${basePath}`;
  const websocketURI = `${rootServerURI.replace(/^http/, 'ws')}/graphql`;

  // Ensure that we use the same `headers` value.
  const headersAsString = JSON.stringify(headers);
  const headerObject = React.useMemo(() => JSON.parse(headersAsString), [headersAsString]);

  const websocketClient = React.useMemo(
    () =>
      new SubscriptionClient(websocketURI, {
        reconnect: true,
        connectionParams: {...headerObject},
      }),
    [headerObject, websocketURI],
  );

  const retryLink = React.useMemo(() => {
    return new RetryLink({
      attempts: {
        max: 3,
        retryIf: async (error, _operation) => {
          if (error && error.statusCode && httpStatusCodesToRetry.has(error.statusCode)) {
            return true;
          }
          return false;
        },
      },

      delay: (_retryCount, _operation, error) => {
        // Retry-after header is in seconds, concert to ms by multiplying by 1000.
        const wait = parseFloat(error?.response?.headers?.get?.('retry-after') ?? '0.3') * 1000;
        return wait;
      },
    });
  }, []);

  const apolloClient = React.useMemo(() => {
    // Subscriptions use WebSocketLink, queries & mutations use HttpLink.
    const splitLink = split(
      ({query}) => {
        const definition = getMainDefinition(query);
        return definition.kind === 'OperationDefinition' && definition.operation === 'subscription';
      },
      new WebSocketLink(websocketClient),
      ApolloLink.from([retryLink, new HttpLink({uri: graphqlPath, headers: headerObject})]),
    );

    return new ApolloClient({
      cache: appCache,
      link: ApolloLink.from([
        ...apolloLinks,
        createOperationQueryStringApolloLink(basePath),
        idempotencyLink,
        splitLink,
      ]),
      defaultOptions: {
        watchQuery: {
          fetchPolicy: 'cache-and-network',
        },
      },
    });
  }, [apolloLinks, appCache, graphqlPath, headerObject, retryLink, websocketClient, basePath]);

  const appContextValue = React.useMemo(
    () => ({
      basePath,
      rootServerURI,
      telemetryEnabled,
      localCacheIdPrefix,
    }),
    [basePath, rootServerURI, telemetryEnabled, localCacheIdPrefix],
  );

  const analytics = React.useMemo(() => dummyAnalytics(), []);
  const instancePageValue = React.useMemo(
    () => ({
      pageTitle: 'Deployment',
      healthTitle: 'Daemons',
    }),
    [],
  );

  return (
    <AppContext.Provider value={appContextValue}>
      <WebSocketProvider websocketClient={websocketClient}>
        <GlobalStyleProvider />
        <ApolloProvider client={apolloClient}>
          <AssetLiveDataProvider>
            <PermissionsProvider>
              <BrowserRouter basename={basePath || ''}>
                <CompatRouter>
                  <TimeProvider>
                    <CodeLinkProtocolProvider>
                      <WorkspaceProvider>
                        <DeploymentStatusProvider include={statusPolling}>
                          <CustomConfirmationProvider>
                            <AnalyticsContext.Provider value={analytics}>
                              <InstancePageContext.Provider value={instancePageValue}>
                                <LayoutProvider>
                                  <DagsterPlusLaunchPromotion />
                                  {props.children}
                                </LayoutProvider>
                              </InstancePageContext.Provider>
                            </AnalyticsContext.Provider>
                          </CustomConfirmationProvider>
                          <CustomTooltipProvider />
                          <CustomAlertProvider />
                          <AssetRunLogObserver />
                        </DeploymentStatusProvider>
                      </WorkspaceProvider>
                    </CodeLinkProtocolProvider>
                  </TimeProvider>
                </CompatRouter>
              </BrowserRouter>
            </PermissionsProvider>
          </AssetLiveDataProvider>
        </ApolloProvider>
      </WebSocketProvider>
    </AppContext.Provider>
  );
};

export const usePrefixedCacheKey = (key: string) => {
  const {localCacheIdPrefix} = useContext(AppContext);
  return `${localCacheIdPrefix}/${key}`;
};
