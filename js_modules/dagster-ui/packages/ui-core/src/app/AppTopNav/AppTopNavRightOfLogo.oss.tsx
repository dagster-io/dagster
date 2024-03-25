import {memo} from 'react';
import {useHistory} from 'react-router-dom';

import {AppTopNavLinks, navLinks} from './AppTopNavLinks';

export const AppTopNavRightOfLogo = memo(() => {
  const history = useHistory();
  return <AppTopNavLinks links={navLinks(history)} />;
});
