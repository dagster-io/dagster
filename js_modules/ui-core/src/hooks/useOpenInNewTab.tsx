import {useCallback, useContext} from 'react';

import {AppContext} from '../app/AppContext';

// Open a path in a new tab. Incorporates the base path to ensure that
// the link opens to the appropriate deployment.
export const useOpenInNewTab = () => {
  const {basePath} = useContext(AppContext);
  return useCallback(
    (path: string) => {
      // eslint-disable-next-line no-restricted-properties
      window.open(`${basePath}${path}`, '_blank');
    },
    [basePath],
  );
};

// Returns true if Cmd (Mac) or Ctrl (Windows/Linux) was held during
// a click or keyboard event, indicating the user wants a new tab.
export function isNewTabClick(e: React.MouseEvent | KeyboardEvent): boolean {
  return 'metaKey' in e && (e.metaKey || e.ctrlKey);
}
