import {useContext} from 'react';

import {AppContext} from '../app/AppContext';

// Open a path in a new tab. Incorporates the base path to ensure that
// the link opens to the appropriate deployment.
export const useOpenInNewTab = () => {
  const {basePath} = useContext(AppContext);
  return (path: string) => {
    window.open(`${basePath}${path}`, '_blank');
  };
};
