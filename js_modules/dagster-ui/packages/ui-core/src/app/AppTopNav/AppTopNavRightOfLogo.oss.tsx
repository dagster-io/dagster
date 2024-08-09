import {memo} from 'react';

import {AppTopNavLinks, navLinks} from './AppTopNavLinks';
import {useJobStateForNav} from './useJobStateForNav';

export const AppTopNavRightOfLogo = memo(() => {
  const jobState = useJobStateForNav();
  return <AppTopNavLinks links={navLinks({jobState})} />;
});
