import {Delayed} from '@dagster-io/ui-components';
import {useRunsRedesignState} from '@shared/app/useRunsRedesignState';

import RunsFeedRoot from './RunsFeedRoot';
import {LoadingSpinner} from '../ui/Loading';
import {lazy} from '../util/lazy';

const RunsPage = lazy(() => import('./redesign/RunsPage'));

export const RunsRoot = () => {
  const runsRedesignState = useRunsRedesignState();

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
