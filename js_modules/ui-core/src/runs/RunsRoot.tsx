import {Delayed} from '@dagster-io/ui-components';
import {useRunsRedesignState} from '@shared/app/useRunsRedesignState';

import RunsFeedRoot from './RunsFeedRoot';
import {useDeclareMobileRouteStatus} from '../app/layout/mobileRouteStatus';
import {LoadingSpinner} from '../ui/Loading';
import {lazy} from '../util/lazy';

const RunsPage = lazy(() => import('./redesign/RunsPage'));

export const RunsRoot = () => {
  const runsRedesignState = useRunsRedesignState();

  // Only the redesign works on mobile; the legacy table keeps the desktop fallback.
  useDeclareMobileRouteStatus(runsRedesignState === 'enabled' ? 'supported' : 'unsupported');

  switch (runsRedesignState) {
    case 'loading':
      return (
        <Delayed>
          <LoadingSpinner purpose="page" />
        </Delayed>
      );
    case 'enabled':
      return <RunsPage />;
    case 'disabled':
      return <RunsFeedRoot />;
  }
};
