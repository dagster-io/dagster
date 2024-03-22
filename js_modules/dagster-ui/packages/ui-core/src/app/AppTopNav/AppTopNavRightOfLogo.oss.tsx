import {memo} from 'react';
import {useHistory} from 'react-router-dom';

import {AppTopNavLinks, useNavLinks} from './AppTopNavLinks';

export const AppTopNavRightOfLogo = memo(() => {
  const history = useHistory();
  const navLinks = useNavLinks(history);
  return <AppTopNavLinks links={navLinks} />;
});
