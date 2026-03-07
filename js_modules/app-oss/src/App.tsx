import {createAppCache} from '@dagster-io/ui-core/app/AppCache';
import {createErrorLink, setupErrorToasts} from '@dagster-io/ui-core/app/AppError';
import {AppLayout} from '@dagster-io/ui-core/app/AppLayout';
import {AppProvider} from '@dagster-io/ui-core/app/AppProvider';
import {ContentRoot} from '@dagster-io/ui-core/app/ContentRoot';
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
          <AppLayout>
            <ContentRoot />
            <Suspense>
              <CommunityNux />
            </Suspense>
          </AppLayout>
        </AppProvider>
      </LiveDataPollRateContext.Provider>
    </RecoilRoot>
  );
}
