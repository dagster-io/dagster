import {memo} from 'react';

import {AppTopNavLinks, navLinks} from '../../../app/AppTopNav/AppTopNavLinks';
import {useJobStateForNav} from '../../../app/AppTopNav/useJobStateForNav';

export const AppTopNavRightOfLogo = memo(() => {
  const jobState = useJobStateForNav();
  return <AppTopNavLinks links={navLinks({jobState})} />;
});
