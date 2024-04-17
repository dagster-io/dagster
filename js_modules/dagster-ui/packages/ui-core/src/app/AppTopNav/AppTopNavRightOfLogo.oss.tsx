import {memo} from 'react';

import {AppTopNavLinks, navLinks} from './AppTopNavLinks';

export const AppTopNavRightOfLogo = memo(() => {
  return <AppTopNavLinks links={navLinks()} />;
});
