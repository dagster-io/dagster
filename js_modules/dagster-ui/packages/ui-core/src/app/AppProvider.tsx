import {
  ApolloClient,
  ApolloLink,
  ApolloProvider,
  HttpLink,
  InMemoryCache,
  split,
} from '@apollo/client';
import {WebSocketLink} from '@apollo/client/link/ws';
import {getMainDefinition} from '@apollo/client/utilities';
import {
  Colors,
  CustomTooltipProvider,
  FontFamily,
  GlobalDialogStyle,
  GlobalInconsolata,
  GlobalInter,
  GlobalPopoverStyle,
  GlobalSuggestStyle,
  GlobalToasterStyle,
  GlobalTooltipStyle,
} from '@dagster-io/ui-components';
import * as React from 'react';
import {BrowserRouter} from 'react-router-dom';
import {CompatRouter} from 'react-router-dom-v5-compat';
import {createGlobalStyle} from 'styled-components';
import {SubscriptionClient} from 'subscriptions-transport-ws';

import {AppContext} from './AppContext';
import {CustomAlertProvider, GlobalCustomAlertPortalStyle} from './CustomAlertProvider';
import {CustomConfirmationProvider} from './CustomConfirmationProvider';
import {LayoutProvider} from './LayoutProvider';
import {PermissionsProvider} from './Permissions';
import {patchCopyToRemoveZeroWidthUnderscores} from './Util';
import {WebSocketProvider} from './WebSocketProvider';
import {AnalyticsContext, dummyAnalytics} from './analytics';
import {migrateLocalStorageKeys} from './migrateLocalStorageKeys';
import {TimeProvider} from './time/TimeContext';
import {AssetLiveDataProvider} from '../asset-data/AssetLiveDataProvider';
import {AssetRunLogObserver} from '../asset-graph/AssetRunLogObserver';
import {DeploymentStatusProvider, DeploymentStatusType} from '../instance/DeploymentStatusProvider';
import {InstancePageContext} from '../instance/InstancePageContext';
import {PerformancePageNavigationListener} from '../performance';
import {JobFeatureProvider} from '../pipelines/JobFeatureContext';
import {WorkspaceProvider} from '../workspace/WorkspaceContext';

import './blueprint.css';

// The solid sidebar and other UI elements insert zero-width spaces so solid names
// break on underscores rather than arbitrary characters, but we need to remove these
// when you copy-paste so they don't get pasted into editors, etc.
patchCopyToRemoveZeroWidthUnderscores();

const GlobalStyle = createGlobalStyle`
  * {
    box-sizing: border-box;
  }

  html, body, #root {
    color-scheme: ${Colors.browserColorScheme()};
    background-color: ${Colors.backgroundDefault()};
    color: ${Colors.textDefault()};
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    display: flex;
    flex: 1 1;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  a,
  a:hover,
  a:active {
    color: ${Colors.linkDefault()};
  }

  #root {
    display: flex;
    flex-direction: column;
    align-items: stretch;
  }

  body {
    margin: 0;
    padding: 0;
  }

  body, input, select, textarea {
    font-family: ${FontFamily.default};
  }

  button {
    color: ${Colors.textDefault()};
    font-family: inherit;
  }

  code, pre {
    font-family: ${FontFamily.monospace};
    font-size: 16px;
  }

  :focus-visible {
    outline: ${Colors.focusRing()} auto 1px;
  }

  :focus:not(:focus-visible) {
    outline: none;
  }

  :not(a):focus,
  :not(a):focus-visible {
    outline-offset: 1px;
  }
`;

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
}

export const AppProvider = (props: AppProviderProps) => {
  const {appCache, config} = props;
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

  const apolloClient = React.useMemo(() => {
    // Subscriptions use WebSocketLink, queries & mutations use HttpLink.
    const splitLink = split(
      ({query}) => {
        const definition = getMainDefinition(query);
        return definition.kind === 'OperationDefinition' && definition.operation === 'subscription';
      },
      new WebSocketLink(websocketClient),
      new HttpLink({uri: graphqlPath, headers: headerObject}),
    );

    return new ApolloClient({
      cache: appCache,
      link: ApolloLink.from([...apolloLinks, splitLink]),
      defaultOptions: {
        watchQuery: {
          fetchPolicy: 'cache-and-network',
        },
      },
    });
  }, [apolloLinks, appCache, graphqlPath, headerObject, websocketClient]);

  const appContextValue = React.useMemo(
    () => ({
      basePath,
      rootServerURI,
      telemetryEnabled,
    }),
    [basePath, rootServerURI, telemetryEnabled],
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
        <GlobalInter />
        <GlobalInconsolata />
        <GlobalStyle />
        <GlobalToasterStyle />
        <GlobalTooltipStyle />
        <GlobalPopoverStyle />
        <GlobalDialogStyle />
        <GlobalCustomAlertPortalStyle />
        <GlobalSuggestStyle />
        <ApolloProvider client={apolloClient}>
          <AssetLiveDataProvider>
            <PermissionsProvider>
              <BrowserRouter basename={basePath || ''}>
                <CompatRouter>
                  <PerformancePageNavigationListener />
                  <TimeProvider>
                    <WorkspaceProvider>
                      <DeploymentStatusProvider include={statusPolling}>
                        <CustomConfirmationProvider>
                          <AnalyticsContext.Provider value={analytics}>
                            <InstancePageContext.Provider value={instancePageValue}>
                              <JobFeatureProvider>
                                <LayoutProvider>{props.children}</LayoutProvider>
                              </JobFeatureProvider>
                            </InstancePageContext.Provider>
                          </AnalyticsContext.Provider>
                        </CustomConfirmationProvider>
                        <CustomTooltipProvider />
                        <CustomAlertProvider />
                        <AssetRunLogObserver />
                      </DeploymentStatusProvider>
                    </WorkspaceProvider>
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
