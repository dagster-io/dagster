import {registerPortalProvider} from '@dagster-io/ui-components/src/components/createToaster';
import {App} from '@dagster-io/ui-core/app/App';
import {createAppCache} from '@dagster-io/ui-core/app/AppCache';
import {errorLink, setupErrorToasts} from '@dagster-io/ui-core/app/AppError';
import {AppProvider} from '@dagster-io/ui-core/app/AppProvider';
import {AppTopNav} from '@dagster-io/ui-core/app/AppTopNav';
import {ContentRoot} from '@dagster-io/ui-core/app/ContentRoot';
import {UserSettingsButton} from '@dagster-io/ui-core/app/UserSettingsButton';
import {logLink, timeStartLink} from '@dagster-io/ui-core/app/apolloLinks';
import {DeploymentStatusType} from '@dagster-io/ui-core/instance/DeploymentStatusProvider';
import React from 'react';
import ReactDOM from 'react-dom';

import {CommunityNux} from './NUX/CommunityNux';
import {extractInitializationData} from './extractInitializationData';
import {telemetryLink} from './telemetryLink';

const {pathPrefix, telemetryEnabled} = extractInitializationData();

const apolloLinks = [logLink, errorLink, timeStartLink];

if (telemetryEnabled) {
  apolloLinks.unshift(telemetryLink(pathPrefix));
}
if (process.env.NODE_ENV === 'development') {
  setupErrorToasts();
}

const config = {
  apolloLinks,
  basePath: pathPrefix,
  origin: process.env.NEXT_PUBLIC_BACKEND_ORIGIN || document.location.origin,
  telemetryEnabled,
  statusPolling: new Set<DeploymentStatusType>(['code-locations', 'daemons']),
};

const appCache = createAppCache();

// eslint-disable-next-line import/no-default-export
export default function AppPage() {
  const [portaledElements, setPortalElements] = React.useState<
    [React.ReactNode, HTMLElement, string | undefined][]
  >([]);
  React.useLayoutEffect(() => {
    registerPortalProvider((node, container, key) => {
      setPortalElements((elements) => {
        return [...elements, [node, container, key]];
      });
    });
  }, []);
  console.log({portaledElements});
  return (
    <AppProvider appCache={appCache} config={config}>
      {portaledElements.map(([node, container, key], index) =>
        ReactDOM.createPortal(node, container, key ?? String(index)),
      )}
      <AppTopNav searchPlaceholder="Search…" allowGlobalReload>
        <UserSettingsButton />
      </AppTopNav>
      <App>
        <ContentRoot />
        <CommunityNux />
      </App>
    </AppProvider>
  );
}
