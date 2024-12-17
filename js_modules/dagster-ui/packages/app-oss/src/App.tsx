import {App} from '@dagster-io/ui-core/app/App';
import {createAppCache} from '@dagster-io/ui-core/app/AppCache';
import {createErrorLink, setupErrorToasts} from '@dagster-io/ui-core/app/AppError';
import {AppProvider} from '@dagster-io/ui-core/app/AppProvider';
import {AppTopNav} from '@dagster-io/ui-core/app/AppTopNav/AppTopNav';
import {ContentRoot} from '@dagster-io/ui-core/app/ContentRoot';
import {HelpMenu} from '@dagster-io/ui-core/app/HelpMenu';
import {UserSettingsButton} from '@dagster-io/ui-core/app/UserSettingsButton';
import {logLink, timeStartLink} from '@dagster-io/ui-core/app/apolloLinks';
import {DeploymentStatusType} from '@dagster-io/ui-core/instance/DeploymentStatusProvider';
import {LiveDataPollRateContext} from '@dagster-io/ui-core/live-data-provider/LiveDataProvider';
import {Suspense} from 'react';
import {RecoilRoot} from 'recoil';

import {CommunityNux} from './NUX/CommunityNux';
import {extractInitializationData} from './extractInitializationData';
import {telemetryLink} from './telemetryLink';

const {pathPrefix, telemetryEnabled, liveDataPollRate, instanceId} = extractInitializationData();

const apolloLinks = [logLink, createErrorLink(true), timeStartLink];

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
  idempotentMutations: false,
};

const appCache = createAppCache();

// eslint-disable-next-line import/no-default-export
export default function AppPage() {
  return (
    <RecoilRoot>
      <LiveDataPollRateContext.Provider value={liveDataPollRate ?? 2000}>
        <AppProvider appCache={appCache} config={config} localCacheIdPrefix={instanceId}>
          <AppTopNav allowGlobalReload>
            <HelpMenu showContactSales={false} />
            <UserSettingsButton />
          </AppTopNav>
          <App>
            <ContentRoot />
            <Suspense>
              <CommunityNux />
            </Suspense>
          </App>
        </AppProvider>
      </LiveDataPollRateContext.Provider>
    </RecoilRoot>
  );
}
