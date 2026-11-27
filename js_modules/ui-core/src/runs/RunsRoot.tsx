import {Delayed} from '@dagster-io/ui-components';
import {useRunsRedesignState} from '@shared/app/useRunsRedesignState';

import RunsFeedRoot from './RunsFeedRoot';
import {useQueryPersistedRunsFeedView} from './RunsFeedUtils';
import {useDeclareMobileRouteStatus} from '../app/layout/mobileRouteStatus';
import {RunsFeedView} from '../graphql/types';
import {LoadingSpinner} from '../ui/Loading';
import {lazy} from '../util/lazy';

const RunsPage = lazy(() => import('./redesign/RunsPage'));

export const RunsRoot = () => {
  const runsRedesignState = useRunsRedesignState();
  const [view] = useQueryPersistedRunsFeedView();

  // The redesign lists only runs for now, so the backfills view stays on the legacy page.
  const showRedesign = runsRedesignState === 'enabled' && view !== RunsFeedView.BACKFILLS;

  // Only the redesign works on mobile; the legacy table keeps the desktop fallback.
  useDeclareMobileRouteStatus(showRedesign ? 'supported' : 'unsupported');

  switch (runsRedesignState) {
    case 'loading':
      return (
        <Delayed>
          <LoadingSpinner purpose="page" />
        </Delayed>
      );
    case 'enabled':
      return showRedesign ? <RunsPage /> : <RunsFeedRoot />;
    case 'disabled':
      return <RunsFeedRoot />;
  }
};
